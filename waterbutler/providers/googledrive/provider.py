import os
import http
import json
import asyncio
from urllib import parse

import furl

from waterbutler.core import utils
from waterbutler.core import streams
from waterbutler.core import provider
from waterbutler.core import exceptions

from waterbutler.providers.googledrive import settings
from waterbutler.providers.googledrive import utils as drive_utils
from waterbutler.providers.googledrive.metadata import GoogleDriveRevision
from waterbutler.providers.googledrive.metadata import GoogleDriveFileMetadata
from waterbutler.providers.googledrive.metadata import GoogleDriveFolderMetadata


class GoogleDrivePath(utils.WaterButlerPath):

    def __init__(self, folder, path, prefix=True, suffix=False):
        super().__init__(path, prefix=prefix, suffix=suffix)
        self._folder = folder
        full_path = os.path.join(folder, path.lstrip('/'))
        self._full_path = self._format_path(full_path)

    @property
    def parent(self):
        cls = self.__class__
        return cls(self._folder, '/'.join(self._parts[:-1]) + '/', prefix=self._prefix, suffix=self._suffix)

    @property
    def child(self):
        cls = self.__class__
        path = '/' + '/'.join(self._parts[2:])
        if self.is_dir:
            path += '/'
        path = path.replace('//', '/')
        return cls(self._folder, path, prefix=self._prefix, suffix=self._suffix)

    @property
    def path(self):
        return parse.unquote(self._path)

    @property
    def parts(self):
        return [parse.unquote(x) for x in self._parts]

    @property
    def name(self):
        return parse.unquote(self._parts[-1])


class GoogleDriveProvider(provider.BaseProvider):

    BASE_URL = settings.BASE_URL

    def __init__(self, auth, credentials, settings):
        super().__init__(auth, credentials, settings)
        self.token = self.credentials['token']
        self.folder = self.settings['folder']

    @property
    def default_headers(self):
        return {'authorization': 'Bearer {}'.format(self.token)}

    @asyncio.coroutine
    def download(self, path, revision=None, **kwargs):
        data = yield from self.metadata(path, raw=True)
        if revision and not revision.endswith(settings.DRIVE_IGNORE_VERSION):
            # Must make additional request to look up download URL for revision
            response = yield from self.make_request(
                'GET',
                self.build_url('files', data['id'], 'revisions', revision, alt='json'),
                expects=(200, ),
                throws=exceptions.MetadataError,
            )
            data = yield from response.json()

        try:
            download_url = data['downloadUrl']
        except KeyError:
            download_url = drive_utils.get_export_link(data['exportLinks'])

        download_resp = yield from self.make_request(
            'GET',
            download_url,
            expects=(200, ),
            throws=exceptions.DownloadError,
        )

        return streams.ResponseStreamReader(download_resp)

    @asyncio.coroutine
    def upload(self, stream, path, **kwargs):
        path = path.split('/')
        path = '/'.join(path[:-1] + [parse.quote(path[-1])])
        path = GoogleDrivePath(self.folder['name'], path)

        try:
            metadata = yield from self.metadata(str(path), raw=True)
            folder_id = metadata['parents'][0]['id']
            segments = (metadata['id'], )
            created = False
        except exceptions.MetadataError:
            if path.parent.is_root:
                folder_id = self.folder['id']
            else:
                parent_path = str(path.parent).rstrip('/')
                metadata = yield from self.metadata(parent_path, raw=True)
                folder_id = metadata['id']
            segments = ()
            created = True
        upload_metadata = self._build_upload_metadata(folder_id, path.name)
        upload_id = yield from self._start_resumable_upload(created, segments, stream.size, upload_metadata)
        data = yield from self._finish_resumable_upload(segments, stream, upload_id)
        return GoogleDriveFileMetadata(data, path.parent).serialized(), created

    @asyncio.coroutine
    def delete(self, path, **kwargs):
        path = GoogleDrivePath(self.folder['name'], path)
        metadata = yield from self.metadata(str(path), raw=True)
        yield from self.make_request(
            'DELETE',
            self.build_url('files', metadata['id']),
            expects=(204, ),
            throws=exceptions.DeleteError,
        )

    def _build_query(self, folder_id, title=None):
        queries = [
            "'{}' in parents".format(folder_id),
            'trashed = false',
        ]
        if title:
            queries.append("title = '{}'".format(title.replace('"', '\\"').replace('\'', '\\\'')))
        return ' and '.join(queries)

    @asyncio.coroutine
    def metadata(self, path, original_path=None, folder_id=None, raw=False, **kwargs):
        path = GoogleDrivePath(self.folder['name'], path)
        original_path = original_path or path
        folder_id = folder_id or self.folder['id']
        child = path.child

        title = None if (path.is_leaf and path.is_dir) else path.parts[1]
        query = self._build_query(folder_id, title=title)

        resp = yield from self.make_request(
            'GET',
            self.build_url('files', q=query, alt='json'),
            expects=(200, ),
            throws=exceptions.MetadataError,
        )
        data = yield from resp.json()

        # Raise 404 on empty results if file or partial lookup
        if not data['items']:
            if path.is_file or not path.is_leaf:
                raise exceptions.MetadataError('{} not found'.format(str(path)), code=http.client.NOT_FOUND)

        if not path.is_leaf:
            child_id = data['items'][0]['id']
            return (yield from self.metadata(str(child), original_path=original_path, folder_id=child_id, raw=raw, **kwargs))

        if path.is_dir:
            return [
                self._serialize_item(original_path, item, raw=raw)
                for item in data['items']
            ]

        # The "version" key does not correspond to revision IDs for Google Docs
        # files; make an extra request to the revisions endpoint to fetch the
        # true ID of the latest revision
        if drive_utils.is_docs_file(data['items'][0]):
            revisions_response = yield from self.make_request(
                'GET',
                self.build_url('files', data['items'][0]['id'], 'revisions'),
                expects=(200, ),
                throws=exceptions.RevisionsError,
            )
            revisions_data = yield from revisions_response.json()

            # Revisions are not available for some sharing configurations. If
            # revisions list is empty, use the etag of the file plus a sentinel
            # string as a dummy revision ID.
            if not revisions_data['items']:
                # If there are no revisions use etag as vid
                data['items'][0]['version'] = revisions_data['etag'] + settings.DRIVE_IGNORE_VERSION
            else:
                data['items'][0]['version'] = revisions_data['items'][-1]['id']

        return self._serialize_item(original_path.parent, data['items'][0], raw=raw)

    @asyncio.coroutine
    def revisions(self, path, **kwargs):
        metadata = yield from self.metadata(path, raw=True)
        response = yield from self.make_request(
            'GET',
            self.build_url('files', metadata['id'], 'revisions'),
            expects=(200, ),
            throws=exceptions.RevisionsError,
        )
        data = yield from response.json()
        if data['items']:
            return [
                GoogleDriveRevision(item).serialized()
                for item in reversed(data['items'])
            ]

        # Use dummy ID if no revisions found
        return [GoogleDriveRevision({
            'modifiedDate': metadata['modifiedDate'],
            'id': data['etag'] + settings.DRIVE_IGNORE_VERSION,
        }).serialized()]

    def _build_upload_url(self, *segments, **query):
        return provider.build_url(settings.BASE_UPLOAD_URL, *segments, **query)

    def _serialize_item(self, path, item, raw=False):
        if raw:
            return item
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            return GoogleDriveFolderMetadata(item, path).serialized()
        return GoogleDriveFileMetadata(item, path).serialized()

    def _build_upload_metadata(self, folder_id, name):
        return {
            'parents': [
                {
                    'kind': 'drive#parentReference',
                    'id': folder_id,
                },
            ],
            'title': name,
        }

    @asyncio.coroutine
    def _start_resumable_upload(self, created, segments, size, metadata):
        resp = yield from self.make_request(
            'POST' if created else 'PUT',
            self._build_upload_url('files', *segments, uploadType='resumable'),
            headers={
                'Content-Type': 'application/json',
                'X-Upload-Content-Length': str(size),
            },
            data=json.dumps(metadata),
            expects=(200, ),
            throws=exceptions.UploadError,
        )
        location = furl.furl(resp.headers['LOCATION'])
        return location.args['upload_id']

    @asyncio.coroutine
    def _finish_resumable_upload(self, segments, stream, upload_id):
        resp = yield from self.make_request(
            'PUT',
            self._build_upload_url('files', *segments, uploadType='resumable', upload_id=upload_id),
            headers={'Content-Length': str(stream.size)},
            data=stream,
            expects=(200, ),
            throws=exceptions.UploadError,
        )
        return (yield from resp.json())

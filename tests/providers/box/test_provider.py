import pytest

from tests.utils import async

import io

import aiohttpretty

from waterbutler.core import streams
from waterbutler.core import exceptions

from waterbutler.providers.box import BoxProvider
from waterbutler.providers.box.provider import BoxPath
from waterbutler.providers.box.metadata import BoxRevision
from waterbutler.providers.box.metadata import BoxFileMetadata


@pytest.fixture
def auth():
    return {
        'name': 'cat',
        'email': 'cat@cat.com',
    }


@pytest.fixture
def credentials():
    return {'token': 'wrote harry potter'}


@pytest.fixture
def settings():
    return {'folder': '11446498'}


@pytest.fixture
def provider(auth, credentials, settings):
    return BoxProvider(auth, credentials, settings)


@pytest.fixture
def file_content():
    return b'SLEEP IS FOR THE WEAK GO SERVE STREAMS'


@pytest.fixture
def file_like(file_content):
    return io.BytesIO(file_content)


@pytest.fixture
def file_stream(file_like):
    return streams.FileStreamReader(file_like)

@pytest.fixture
def folder_object_metadata():
    return {
        "type": "folder",
        "id": "11446498",
        "sequence_id": "1",
        "etag": "1",
        "name": "Pictures",
        "created_at": "2012-12-12T10:53:43-08:00",
        "modified_at": "2012-12-12T11:15:04-08:00",
        "description": "Some pictures I took",
        "size": 629644,
        "path_collection": {
            "total_count": 1,
            "entries": [
                {
                    "type": "folder",
                    "id": "0",
                    "sequence_id": None,
                    "etag": None,
                    "name": "All Files"
                }
            ]
        },
        "created_by": {
            "type": "user",
            "id": "17738362",
            "name": "sean rose",
            "login": "sean@box.com"
        },
        "modified_by": {
            "type": "user",
            "id": "17738362",
            "name": "sean rose",
            "login": "sean@box.com"
        },
        "owned_by": {
            "type": "user",
            "id": "17738362",
            "name": "sean rose",
            "login": "sean@box.com"
        },
        "shared_link": {
            "url": "https://www.box.com/s/vspke7y05sb214wjokpk",
            "download_url": None,
            "vanity_url": None,
            "is_password_enabled": False,
            "unshared_at": None,
            "download_count": 0,
            "preview_count": 0,
            "access": "open",
            "permissions": {
                "can_download": True,
                "can_preview": True
            }
        },
        "folder_upload_email": {
            "access": "open",
            "email": "upload.Picture.k13sdz1@u.box.com"
        },
        "parent": {
            "type": "folder",
            "id": "0",
            "sequence_id": None,
            "etag": None,
            "name": "All Files"
        },
        "item_status": "active",
        "item_collection": {
            "total_count": 1,
            "entries": [
                {
                    "type": "file",
                    "id": "5000948880",
                    "sequence_id": "3",
                    "etag": "3",
                    "sha1": "134b65991ed521fcfe4724b7d814ab8ded5185dc",
                    "name": "tigers.jpeg"
                }
            ],
            "offset": 0,
            "limit": 100
        },
        "tags": [
            "approved",
            "ready to publish"
        ]
    }


@pytest.fixture
def folder_list_metadata():
    return {
        "total_count": 24,
        "entries": [
            {
                "type": "folder",
                "id": "192429928",
                "sequence_id": "1",
                "etag": "1",
                "name": "Stephen Curry Three Pointers"
            },
            {
                "type": "file",
                "id": "818853862",
                "sequence_id": "0",
                "etag": "0",
                "name": "Warriors.jpg"
            }
        ],
        "offset": 0,
        "limit": 2,
        "order": [
            {
                "by": "type",
                "direction": "ASC"
            },
            {
                "by": "name",
                "direction": "ASC"
            }
        ]
    }


@pytest.fixture
def file_metadata():
    return {
        'entries': [
            {
                "type": "file",
                "id": "5000948880",
                "sequence_id": "3",
                "etag": "3",
                "sha1": "134b65991ed521fcfe4724b7d814ab8ded5185dc",
                "name": "tigers.jpeg",
                "description": "a picture of tigers",
                "size": 629644,
                "path_collection": {
                    "total_count": 2,
                    "entries": [
                        {
                            "type": "folder",
                            "id": "0",
                            "sequence_id": None,
                            "etag": None,
                            "name": "All Files"
                        },
                        {
                            "type": "folder",
                            "id": "11446498",
                            "sequence_id": "1",
                            "etag": "1",
                            "name": "Pictures"
                        }
                    ]
                },
                "created_at": "2012-12-12T10:55:30-08:00",
                "modified_at": "2012-12-12T11:04:26-08:00",
                "created_by": {
                    "type": "user",
                    "id": "17738362",
                    "name": "sean rose",
                    "login": "sean@box.com"
                },
                "modified_by": {
                    "type": "user",
                    "id": "17738362",
                    "name": "sean rose",
                    "login": "sean@box.com"
                },
                "owned_by": {
                    "type": "user",
                    "id": "17738362",
                    "name": "sean rose",
                    "login": "sean@box.com"
                },
                "shared_link": {
                    "url": "https://www.box.com/s/rh935iit6ewrmw0unyul",
                    "download_url": "https://www.box.com/shared/static/rh935iit6ewrmw0unyul.jpeg",
                    "vanity_url": None,
                    "is_password_enabled": False,
                    "unshared_at": None,
                    "download_count": 0,
                    "preview_count": 0,
                    "access": "open",
                    "permissions": {
                        "can_download": True,
                        "can_preview": True
                    }
                },
                "parent": {
                    "type": "folder",
                    "id": "11446498",
                    "sequence_id": "1",
                    "etag": "1",
                    "name": "Pictures"
                },
                "item_status": "active"
            }
        ]
    }


@pytest.fixture
def revisions_list_metadata():
    return {
        'entries': [
            {'name': 'lode.txt', 'modified_by': {'login': 'jmcarp@umich.edu', 'id': '183920511', 'type': 'user', 'name': 'Joshua Carp'}, 'modified_at': '2015-02-24T09:26:02-08:00', 'size': 1620, 'id': '25065971851', 'sha1': 'f313795ea4184ddbb7d12d3691d1850b83fe9b3c', 'type': 'file_version', 'created_at': '2015-02-24T09:26:02-08:00'},
        ],
        'limit': 1000,
        'offset': 0,
        'total_count': 1,
    }


class TestCRUD:

    @async
    @pytest.mark.aiohttpretty
    def test_download(self, provider, file_metadata):
        item = file_metadata['entries'][0]
        path = BoxPath('/' + item['id'] + '/triangles.txt')
        metadata_url = provider.build_url('files', item['id'])
        content_url = provider.build_url('files', item['id'], 'content')
        aiohttpretty.register_json_uri('GET', metadata_url, body=item)
        aiohttpretty.register_uri('GET', content_url, body=b'better')
        result = yield from provider.download(str(path))
        content = yield from result.response.read()

        assert content == b'better'

    @async
    @pytest.mark.aiohttpretty
    def test_download_not_found(self, provider, file_metadata):
        item = file_metadata['entries'][0]
        path = BoxPath('/' + item['id'] + '/vectors.txt')
        metadata_url = provider.build_url('files', item['id'])
        aiohttpretty.register_uri('GET', metadata_url, status=404)

        with pytest.raises(exceptions.ProviderError):
            yield from provider.download(str(path))

    @async
    @pytest.mark.aiohttpretty
    def test_upload_create(self, provider, folder_object_metadata, folder_list_metadata, file_metadata, file_stream, settings):
        path = BoxPath('/' + provider.folder + '/newfile')
        folder_object_url = provider.build_url('folders', path._id)
        folder_list_url = provider.build_url('folders', path._id, 'items')
        upload_url = provider._build_upload_url('files', 'content')
        aiohttpretty.register_json_uri('GET', folder_object_url, body=folder_object_metadata)
        aiohttpretty.register_json_uri('GET', folder_list_url, body=folder_list_metadata)
        aiohttpretty.register_json_uri('POST', upload_url, status=201, body=file_metadata)
        metadata, created = yield from provider.upload(file_stream, str(path))
        file_metadata['entries'][0]['fullPath'] = '/Pictures/newfile'
        expected = BoxFileMetadata(file_metadata['entries'][0], provider.folder).serialized()

        assert metadata == expected
        assert created is True
        assert aiohttpretty.has_call(method='GET', uri=folder_object_url)
        assert aiohttpretty.has_call(method='GET', uri=folder_list_url)
        assert aiohttpretty.has_call(method='POST', uri=upload_url)

    @async
    @pytest.mark.aiohttpretty
    def test_upload_update(self, provider, folder_object_metadata, folder_list_metadata, file_metadata, file_stream, settings):
        item = folder_list_metadata['entries'][0]
        path = BoxPath('/' + provider.folder + '/' + item['name'])
        folder_object_url = provider.build_url('folders', path._id)
        folder_list_url = provider.build_url('folders', path._id, 'items')
        upload_url = provider._build_upload_url('files', item['id'], 'content')
        aiohttpretty.register_json_uri('GET', folder_object_url, body=folder_object_metadata)
        aiohttpretty.register_json_uri('GET', folder_list_url, body=folder_list_metadata)
        aiohttpretty.register_json_uri('POST', upload_url, status=201, body=file_metadata)
        metadata, created = yield from provider.upload(file_stream, str(path))
        file_metadata['entries'][0]['fullPath'] = '/Pictures/Stephen Curry Three Pointers'
        expected = BoxFileMetadata(file_metadata['entries'][0], provider.folder).serialized()

        assert metadata == expected
        assert created is False
        assert aiohttpretty.has_call(method='GET', uri=folder_object_url)
        assert aiohttpretty.has_call(method='GET', uri=folder_list_url)
        assert aiohttpretty.has_call(method='POST', uri=upload_url)

    @async
    @pytest.mark.aiohttpretty
    def test_delete_file(self, provider, file_metadata):
        item = file_metadata['entries'][0]
        path = BoxPath('/' + item['id'] + '/' + item['name'])
        url = provider.build_url('files', path._id)
        aiohttpretty.register_json_uri('GET', url, body=item)
        aiohttpretty.register_uri('DELETE', url, status=204)
        yield from provider.delete(str(path))

        assert aiohttpretty.has_call(method='DELETE', uri=url)


class TestMetadata:

    @async
    @pytest.mark.aiohttpretty
    def test_metadata(self, provider, folder_object_metadata, folder_list_metadata):
        path = BoxPath('/' + provider.folder + '/')
        object_url = provider.build_url('folders', provider.folder)
        list_url = provider.build_url('folders', provider.folder, 'items')
        aiohttpretty.register_json_uri('GET', object_url, body=folder_object_metadata)
        aiohttpretty.register_json_uri('GET', list_url, body=folder_list_metadata)

        result = yield from provider.metadata(str(path))

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[1]['kind'] == 'file'
        assert result[1]['name'] == 'Warriors.jpg'
        assert result[1]['path'] == '/818853862/Warriors.jpg'

    @async
    @pytest.mark.aiohttpretty
    def test_metadata_not_child(self, provider, folder_object_metadata):
        provider.folder += 'yourenotmydad'
        path = BoxPath('/' + provider.folder + '/')
        object_url = provider.build_url('folders', provider.folder)
        aiohttpretty.register_json_uri('GET', object_url, body=folder_object_metadata)

        with pytest.raises(exceptions.MetadataError) as exc_info:
            yield from provider.metadata(str(path))
        assert exc_info.value.code == 404

    @async
    @pytest.mark.aiohttpretty
    def test_metadata_root_file(self, provider, file_metadata):
        path = BoxPath('/' + provider.folder + '/pfile')
        url = provider.build_url('files', path._id)
        aiohttpretty.register_json_uri('GET', url, body=file_metadata['entries'][0])
        result = yield from provider.metadata(str(path))

        assert isinstance(result, dict)
        assert result['kind'] == 'file'
        assert result['name'] == 'tigers.jpeg'
        assert result['path'] == '/5000948880/tigers.jpeg'

    @async
    @pytest.mark.aiohttpretty
    def test_metadata_nested(self, provider, file_metadata):
        item = file_metadata['entries'][0]
        file_id = item['id']
        path = BoxPath('/' + file_id + '/name.txt')
        file_url = provider.build_url('files', file_id)
        aiohttpretty.register_json_uri('GET', file_url, body=item)
        result = yield from provider.metadata(str(path))

        expected = BoxFileMetadata(item, provider.folder).serialized()
        assert result == expected
        assert aiohttpretty.has_call(method='GET', uri=file_url)

    @async
    @pytest.mark.aiohttpretty
    def test_metadata_missing(self, provider):
        path = BoxPath('/' + provider.folder + '/pfile')
        url = provider.build_url('files', path._id)
        aiohttpretty.register_uri('GET', url, status=404)

        with pytest.raises(exceptions.MetadataError):
            yield from provider.metadata(str(path))


class TestRevisions:

    @async
    @pytest.mark.aiohttpretty
    def test_get_revisions(self, provider, file_metadata, revisions_list_metadata):
        item = file_metadata['entries'][0]
        file_id = item['id']
        path = BoxPath('/' + file_id)
        file_url = provider.build_url('files', item['id'])
        revisions_url = provider.build_url('files', file_id, 'versions')
        aiohttpretty.register_json_uri('GET', file_url, body=item)
        aiohttpretty.register_json_uri('GET', revisions_url, body=revisions_list_metadata)

        result = yield from provider.revisions(str(path))
        expected = [
            BoxRevision(each).serialized()
            for each in [item] + revisions_list_metadata['entries']
        ]
        assert result == expected
        assert aiohttpretty.has_call(method='GET', uri=file_url)
        assert aiohttpretty.has_call(method='GET', uri=revisions_url)

    @async
    @pytest.mark.aiohttpretty
    def test_get_revisions_free_account(self, provider, file_metadata):
        item = file_metadata['entries'][0]
        file_id = item['id']
        path = BoxPath('/' + file_id)
        file_url = provider.build_url('files', item['id'])
        revisions_url = provider.build_url('files', file_id, 'versions')
        aiohttpretty.register_json_uri('GET', file_url, body=item)
        aiohttpretty.register_json_uri('GET', revisions_url, body={}, status=403)

        result = yield from provider.revisions(str(path))
        expected = [BoxRevision(item).serialized()]
        assert result == expected
        assert aiohttpretty.has_call(method='GET', uri=file_url)
        assert aiohttpretty.has_call(method='GET', uri=revisions_url)

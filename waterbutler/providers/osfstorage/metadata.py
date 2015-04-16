from waterbutler.core import metadata

class BaseOsfStorageMetadata:
    @property
    def provider(self):
        return 'osfstorage'


class OsfStorageFileMetadata(BaseOsfStorageMetadata, metadata.BaseFileMetadata):

    @property
    def name(self):
        return self.raw['name']

    @property
    def path(self):
        return self.raw['path']

    @property
    def modified(self):
        return self.raw.get('modified')

    @property
    def size(self):
        return self.raw.get('size')

    @property
    def full_path(self):
        return self.raw.get('fullPath')

    @property
    def content_type(self):
        return None

    @property
    def extra(self):
        return {
            key: self.raw[key]
            for key in
            ('version', 'downloads')
            if key in self.raw
        }


class OsfStorageFolderMetadata(BaseOsfStorageMetadata, metadata.BaseFolderMetadata):

    @property
    def name(self):
        return self.raw['name']

    @property
    def path(self):
        return self.raw['path']


class OsfStorageRevisionMetadata(BaseOsfStorageMetadata, metadata.BaseFileRevisionMetadata):

    @property
    def modified(self):
        return self.raw['date']

    @property
    def version_identifier(self):
        return 'version'

    @property
    def version(self):
        return str(self.raw['index'])

    @property
    def extra(self):
        return {
            'user': self.raw['user'],
            'downloads': self.raw['downloads'],
        }

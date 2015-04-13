import abc


class BaseMetadata(metaclass=abc.ABCMeta):
    """The BaseMetadata object provides structure
    for all metadata returned via WaterButler
    """

    def __init__(self, raw):
        self.raw = raw

    def serialized(self):
        """The JSON serialization of metadata from WaterButler.
        .. warning::

            This method determines the output of the REST API
        """
        return {
            'provider': self.provider,
            'kind': self.kind,
            'name': self.name,
            'path': self.path,
            'fullPath': self.full_path,
            'extra': self.extra,
        }

    def build_path(self, path):
        if not path.startswith('/'):
            path = '/' + path
        if self.kind == 'folder' and not path.endswith('/'):
            path += '/'
        return path

    @abc.abstractproperty
    def provider(self):
        """The provider from which this resource
        originated.
        """
        pass

    @abc.abstractproperty
    def kind(self):
        """`file` or `folder`"""
        pass

    @abc.abstractproperty
    def name(self):
        """The name to show a users
        ::
            /bar/foo.txt -> foo.txt
            /<someid> -> whatever.png
        """
        pass

    @abc.abstractproperty
    def path(self):
        """The canonical string representation
        of a waterbutler file or folder.

        ..note::
            All paths MUST start with a `/`
            All Folders MUST end with a `/`
        """
        pass

    @property
    def full_path(self):
        """The "pretty" variant of path
        this path can be displayed to the enduser

        path -> /Folder%20Name/123abc
        full_path -> /Folder Name/File Name

        ..note::
            All paths MUST start with a `/`
            All Folders MUST end with a `/`
        ..note::
            Defaults to self.path
        """
        return self.path

    @property
    def extra(self):
        return {}


class BaseFileMetadata(BaseMetadata):

    def serialized(self):
        return dict(super().serialized(), **{
            'contentType': self.content_type,
            'modified': self.modified,
            'size': self.size,
        })

    @property
    def kind(self):
        """File"""
        return 'file'

    @abc.abstractproperty
    def content_type(self):
        pass

    @abc.abstractproperty
    def modified(self):
        pass

    @abc.abstractproperty
    def size(self):
        pass


class BaseFileRevisionMetadata(metaclass=abc.ABCMeta):

    def __init__(self, raw):
        self.raw = raw
    def serialized(self):
        return {
            'extra': self.extra,
            'version': self.version,
            'modified': self.modified,
            'versionIdentifier': self.version_identifier,
        }

    @abc.abstractproperty
    def modified(self):
        pass

    @abc.abstractproperty
    def version(self):
        pass

    @abc.abstractproperty
    def version_identifier(self):
        pass

    @property
    def extra(self):
        return {}


class BaseFolderMetadata(BaseMetadata):
    """Defines that metadata structure for
    folders, auto defines :func:`kind`
    """

    @property
    def kind(self):
        return 'folder'

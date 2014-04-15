import mock

from webtest_plus import TestApp

import website
from website.addons.base.testing import AddonTestCase
from website.addons.dataverse.dvn.connection import DvnConnection
from website.addons.dataverse.dvn.dataverse import Dataverse
from website.addons.dataverse.dvn.study import Study
from website.addons.dataverse.dvn.file import DvnFile

app = website.app.init_app(
    routes=True, set_backends=False, settings_module='website.settings'
)


class DataverseAddonTestCase(AddonTestCase):
    ADDON_SHORT_NAME = 'dataverse'

    def create_app(self):
        return TestApp(app)

    def set_user_settings(self, settings):
        settings.dataverse_username = 'snowman'
        settings.dataverse_password = 'frosty'

    def set_node_settings(self, settings):
        settings.dataverse_username = 'snowman'
        settings.dataverse_password = 'frosty'
        settings.dataverse_alias = 'ALIAS2'
        settings.dataverse = 'Example 2'
        settings.study_hdl = 'DVN/00001'
        settings.study = 'Example (DVN/00001)'

def create_mock_connection(username='snowman', password='frosty'):
    """
    Create a mock dataverse connection.

    Pass any credentials other than the default parameters and the connection
    will fail.
    """

    mock_connection = mock.create_autospec(DvnConnection)

    mock_connection.username = username
    mock_connection.password = password

    mock_connection.get_dataverses.return_value = [
        create_mock_dataverse('Example 1'),
        create_mock_dataverse('Example 2'),
        create_mock_dataverse('Example 3')
    ]

    def _get_dataverse(alias):
        return next(
            dataverse for dataverse in mock_connection.get_dataverses()
            if dataverse.title[-1] == alias[-1]
        )

    mock_connection.get_dataverse = mock.MagicMock(
        side_effect=_get_dataverse
    )
    mock_connection.get_dataverse.return_value = create_mock_dataverse()

    if username=='snowman' and password=='frosty':
        return mock_connection


def create_mock_dataverse(title='Example Dataverse 0'):

    mock_dataverse = mock.create_autospec(Dataverse)

    type(mock_dataverse).title = mock.PropertyMock(return_value=title)
    type(mock_dataverse).alias = mock.PropertyMock(
        return_value='ALIAS{}'.format(title[-1]))

    mock_dataverse.get_studies.return_value = [
        create_mock_study('DVN/00001'),
        create_mock_study('DVN/00002'),
        create_mock_study('DVN/00003')
    ]

    def _get_study_by_hdl(hdl):
        return next(
            study for study in mock_dataverse.get_studies()
            if study.get_id() == hdl
        )

    mock_dataverse.get_study_by_hdl = mock.MagicMock(
        side_effect=_get_study_by_hdl
    )

    return mock_dataverse


def create_mock_study(id='DVN/12345'):
    mock_study = mock.create_autospec(Study)

    mock_study.get_id.return_value = id
    mock_study.title = 'Example ({0})'.format(id)
    mock_study.doi = 'doi:12.3456/{0}'.format(id)

    mock_study.get_files.return_value = [create_mock_dvn_file()]
    mock_study.get_file.return_value = create_mock_dvn_file()
    mock_study.get_file_by_id.return_value = create_mock_dvn_file()

    # Fail if not given a valid ID
    if 'DVN' in id:
        return mock_study

def create_mock_dvn_file(id='54321'):
    mock_file = mock.create_autospec(DvnFile)

    mock_file.name = 'file.txt'
    mock_file.id = id

    return mock_file

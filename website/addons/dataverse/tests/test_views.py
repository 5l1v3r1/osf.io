import nose
import unittest
from nose.tools import *
import mock
import json

import httplib as http
from tests.base import URLLookup
from tests.factories import AuthUserFactory
from webtest import Upload
from website.addons.dataverse.settings import HOST
from website.addons.dataverse.views.crud import scrape_dataverse

from utils import create_mock_connection, create_mock_dvn_file,\
    DataverseAddonTestCase, app

lookup = URLLookup(app)


class TestDataverseViewsAuth(DataverseAddonTestCase):

    @mock.patch('website.addons.dataverse.views.auth.connect')
    def test_authorize(self, mock_connection):
        mock_connection.return_value = create_mock_connection()

        url = lookup('api', 'authorize_dataverse',
                     pid=self.project._primary_key)
        self.app.post_json(url, auth=self.user.auth)

        self.node_settings.reload()

        assert_equal(self.node_settings.user, self.user)
        assert_equal(self.node_settings.user_settings, self.user_settings)
        assert_equal(self.node_settings.dataverse_username, 'snowman')
        assert_equal(self.node_settings.dataverse_password, 'frosty')

    @mock.patch('website.addons.dataverse.views.auth.connect')
    def test_authorize_fail(self, mock_connection):
        mock_connection.return_value = create_mock_connection('wrong', 'info')

        url = lookup('api', 'authorize_dataverse',
                     pid=self.project._primary_key)
        res = self.app.post_json(url, auth=self.user.auth, expect_errors=True)
        assert_equal(res.status_code, http.BAD_REQUEST)

    def test_deauthorize(self):
        url = lookup('api', 'deauthorize_dataverse',
                     pid=self.project._primary_key)
        self.app.post_json(url, auth=self.user.auth)

        self.node_settings.reload()
        assert_false(self.node_settings.dataverse_username)
        assert_false(self.node_settings.dataverse_password)
        assert_false(self.node_settings.dataverse_alias)
        assert_false(self.node_settings.dataverse)
        assert_false(self.node_settings.study_hdl)
        assert_false(self.node_settings.study)
        assert_false(self.node_settings.user)

    def test_delete_user(self):
        url = '/api/v1/settings/dataverse/'

        # Non-authorized user can't delete
        user2 = AuthUserFactory()
        self.app.delete_json(url, auth=user2.auth, expect_errors=True)
        self.user_settings.reload()
        assert_true(self.user_settings.dataverse_username)

        # Aurthoized user can delete
        self.app.delete_json(url, auth=self.user.auth)

        # User is no longer authorized
        self.user_settings.reload()
        assert_false(self.user_settings.dataverse_username)
        assert_false(self.user_settings.dataverse_password)

        # User's authorized nodes are now deauthorized
        self.node_settings.reload()
        assert_false(self.node_settings.dataverse_username)
        assert_false(self.node_settings.dataverse_password)
        assert_false(self.node_settings.dataverse_alias)
        assert_false(self.node_settings.dataverse)
        assert_false(self.node_settings.study_hdl)
        assert_false(self.node_settings.study)
        assert_false(self.node_settings.user)


class TestDataverseViewsConfig(DataverseAddonTestCase):

    @mock.patch('website.addons.dataverse.views.config.connect')
    def test_set_user_config(self, mock_connection):

        mock_connection.return_value = create_mock_connection()

        # Create a user with no settings
        user = AuthUserFactory()
        user.add_addon('dataverse')
        user_settings = user.get_addon('dataverse')

        url = '/api/v1/settings/dataverse/'
        params = {'dataverse_username': 'snowman',
                  'dataverse_password': 'frosty'}

        # Post dataverse credentials
        self.app.post_json(url, params, auth=user.auth)
        user_settings.reload()

        # User settings have updated correctly
        assert_equal(user_settings.dataverse_username, 'snowman')
        assert_equal(user_settings.dataverse_password, 'frosty')

    @mock.patch('website.addons.dataverse.views.config.connect')
    def test_set_user_config_fail(self, mock_connection):

        mock_connection.return_value = create_mock_connection('wrong', 'info')

        # Create a user with no settings
        user = AuthUserFactory()
        user.add_addon('dataverse')
        user_settings = user.get_addon('dataverse')

        url = '/api/v1/settings/dataverse/'
        params = {'dataverse_username': 'wrong',
                  'dataverse_password': 'info'}

        # Post incorrect credentials to existing user
        res = self.app.post_json(url, params, auth=self.user.auth,
                                 expect_errors=True)
        self.user_settings.reload()

        # Original user's info has not changed
        assert_equal(res.status_code, http.UNAUTHORIZED)
        assert_equal(self.user_settings.dataverse_username, 'snowman')
        assert_equal(self.user_settings.dataverse_password, 'frosty')

        # Post incorrect credentials to new user
        res = self.app.post_json(url, params, auth=user.auth,
                                 expect_errors=True)
        user_settings.reload()

        # New user's incorrect credentials were not saved
        assert_equal(res.status_code, http.UNAUTHORIZED)
        assert_equal(user_settings.dataverse_username, None)
        assert_equal(user_settings.dataverse_password, None)

    @mock.patch('website.addons.dataverse.views.config.connect')
    def test_set_dataverse(self, mock_connection):
        mock_connection.return_value = create_mock_connection()

        url = lookup('api', 'set_dataverse', pid=self.project._primary_key)
        params = {'dataverse_alias': 'ALIAS1'}

        # Select a different dataverse
        self.app.post_json(url, params, auth=self.user.auth)
        self.project.reload()
        self.node_settings.reload()

        # Dataverse has changed
        assert_equal(self.node_settings.dataverse_alias, 'ALIAS1')
        assert_equal(self.node_settings.dataverse, 'Example 1')

        # Study was unselected
        assert_equal(self.node_settings.study, None)
        assert_equal(self.node_settings.study_hdl, None)

        # Log states that a study was unselected
        last_log = self.project.logs[-1]
        assert_equal(last_log.action, 'dataverse_study_unlinked')
        log_params = last_log.params
        assert_equal(log_params['node'], self.project._primary_key)
        assert_equal(log_params['dataverse']['dataverse'], 'Example 2')
        assert_equal(log_params['dataverse']['study'],
                     'Example (DVN/00001)')

    @mock.patch('website.addons.dataverse.views.config.connect')
    def test_set_dataverse_to_none(self, mock_connection):
        mock_connection.return_value = create_mock_connection()

        url = lookup('api', 'set_dataverse', pid=self.project._primary_key)
        params = {'dataverse_alias': 'None'}

        # Set dataverse to none
        self.app.post_json(url, params, auth=self.user.auth)
        self.project.reload()
        self.node_settings.reload()

        # Dataverse has changed
        assert_equal(self.node_settings.dataverse_alias, None)
        assert_equal(self.node_settings.dataverse, None)

        # Study was unselected
        assert_equal(self.node_settings.study, None)
        assert_equal(self.node_settings.study_hdl, None)

        # Log states that a study was unselected
        last_log = self.project.logs[-1]
        assert_equal(last_log.action, 'dataverse_study_unlinked')
        log_params = last_log.params
        assert_equal(log_params['node'], self.project._primary_key)
        assert_equal(log_params['dataverse']['dataverse'], 'Example 2')
        assert_equal(log_params['dataverse']['study'],
                     'Example (DVN/00001)')

    @mock.patch('website.addons.dataverse.views.config.connect')
    def test_set_study(self, mock_connection):
        mock_connection.return_value = create_mock_connection()

        url = lookup('api', 'set_study', pid=self.project._primary_key)
        params = {'study_hdl': 'DVN/00002'}

        # Select a different study
        self.app.post_json(url, params, auth=self.user.auth)
        self.project.reload()
        self.node_settings.reload()

        # New study was selected, dataverse was unchanged
        assert_equal(self.node_settings.dataverse_alias, 'ALIAS2')
        assert_equal(self.node_settings.study, 'Example (DVN/00002)')
        assert_equal(self.node_settings.study_hdl, 'DVN/00002')

        # Log states that a study was selected
        last_log = self.project.logs[-1]
        assert_equal(last_log.action, 'dataverse_study_linked')
        log_params = last_log.params
        assert_equal(log_params['node'], self.project._primary_key)
        assert_equal(log_params['dataverse']['dataverse'], 'Example 2')
        assert_equal(log_params['dataverse']['study'],
                     'Example (DVN/00002)')

    @mock.patch('website.addons.dataverse.views.config.connect')
    def test_set_study_to_none(self, mock_connection):
        mock_connection.return_value = create_mock_connection()

        url = lookup('api', 'set_study', pid=self.project._primary_key)
        params = {'study_hdl': 'None'}

        # Set study to none
        self.app.post_json(url, params, auth=self.user.auth)
        self.project.reload()
        self.node_settings.reload()

        # Study is none, dataverse is unchanged
        assert_equal(self.node_settings.dataverse_alias, 'ALIAS2')
        assert_equal(self.node_settings.study, None)
        assert_equal(self.node_settings.study_hdl, None)

        # Log states that a study was unselected
        last_log = self.project.logs[-1]
        assert_equal(last_log.action, 'dataverse_study_unlinked')
        log_params = last_log.params
        assert_equal(log_params['node'], self.project._primary_key)
        assert_equal(log_params['dataverse']['dataverse'], 'Example 2')
        assert_equal(log_params['dataverse']['study'],
                     'Example (DVN/00001)')


class TestDataverseViewsCrud(DataverseAddonTestCase):

    @mock.patch('website.addons.dataverse.views.crud.connect')
    @mock.patch('website.addons.dataverse.views.crud.delete_file')
    @mock.patch('website.addons.dataverse.views.crud.get_file_by_id',
                side_effect=[create_mock_dvn_file('54321'), None])
    def test_delete_file(self, mock_get, mock_delete, mock_connection):
        mock_get.return_value = None
        mock_connection.return_value = create_mock_connection()

        path = '54321'
        url = lookup('api', 'dataverse_delete_file',
                     pid=self.project._primary_key, path=path)

        res = self.app.delete(url=url, auth=self.user.auth)

        mock_delete.assert_called_once
        assert_equal(path, mock_delete.call_args[0][0].id)

    @mock.patch('website.addons.dataverse.views.crud.connect')
    @mock.patch('website.addons.dataverse.views.crud.upload_file')
    @mock.patch('website.addons.dataverse.views.crud.get_file',
                side_effect=[None, create_mock_dvn_file()])
    def test_upload_file(self, mock_get, mock_upload, mock_connection):
        mock_upload.return_value = {}
        mock_connection.return_value = create_mock_connection()

        # Define payload
        filename = 'myfile.rst'
        content = b'baz'
        path = '54321'
        payload = {'file': Upload(filename, content,'text/x-rst')}

        # Upload the file
        url = lookup('api', 'dataverse_upload_file',
                     pid=self.project._primary_key, path=path)
        res = self.app.post(url, payload, auth=self.user.auth)

        # File was uploaded
        assert_equal(res.status_code, http.CREATED)
        mock_upload.assert_called_once

        # Parameters are correct
        assert_equal(self.node_settings.study_hdl,
                     mock_upload.call_args[0][0].get_id())
        assert_equal(filename, mock_upload.call_args[0][1])
        assert_equal(content, mock_upload.call_args[0][2])
        assert_equal('file_uploaded', json.loads(res.body)['actionTaken'])

    @mock.patch('website.addons.dataverse.views.crud.connect')
    @mock.patch('website.addons.dataverse.views.crud.upload_file')
    @mock.patch('website.addons.dataverse.views.crud.delete_file')
    @mock.patch('website.addons.dataverse.views.crud.get_file')
    def test_upload_existing(self, mock_get, mock_delete, mock_upload,
                             mock_connection):
        mock_get.return_value = create_mock_dvn_file() # File already exists
        mock_upload.return_value = {}
        mock_connection.return_value = create_mock_connection()

        # Define payload
        filename = 'myfile.rst'
        content = b'baz'
        path = '54321'
        payload = {'file': Upload(filename, content,'text/x-rst')}

        # Attempt to upload the file
        url = lookup('api', 'dataverse_upload_file',
                     pid=self.project._primary_key, path=path)
        res = self.app.post(url, payload, auth=self.user.auth)

        # Old file was deleted
        mock_delete.assert_called_once

        # File was uploaded
        assert_equal(res.status_code, http.CREATED)
        mock_upload.assert_called_once

        # Parameters are correct
        assert_equal(self.node_settings.study_hdl,
                     mock_upload.call_args[0][0].get_id())
        assert_equal(filename, mock_upload.call_args[0][1])
        assert_equal(content, mock_upload.call_args[0][2])
        assert_equal('file_updated', json.loads(res.body)['actionTaken'])

    @mock.patch('website.addons.dataverse.views.crud.connect')
    def test_dataverse_view_file(self, mock_connection):
        mock_connection.return_value = create_mock_connection()

        url = lookup('web', 'dataverse_view_file',
                     pid=self.project._primary_key, path='foo')
        res = self.app.get(url, auth=self.user.auth).maybe_follow()
        assert_equal(res.status_code, 200)

    def test_download_file(self):
        path = 'foo'
        url = lookup('api', 'dataverse_download_file',
                     pid=self.project._primary_key, path=path)
        res = self.app.get(url, auth=self.user.auth)
        assert_equal(
            res.headers.get('location'),
            'http://{0}/dvn/FileDownload/?fileId={1}'.format(HOST, path),
        )


    @unittest.skip('Finish this')
    def test_render_file(self):
        assert 0, 'finish me'

    @unittest.skip('Finish this')
    def test_scrape_dataverse(self):
        assert 0, 'finish me'
        # content = scrape_dataverse(2362170)
        # assert_not_in('IQSS', content)
        # assert_in('%esp', content)

if __name__=='__main__':
    nose.run()
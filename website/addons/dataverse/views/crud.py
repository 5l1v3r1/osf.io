import os
import datetime
import logging
import requests
from bs4 import BeautifulSoup

from framework import request, make_response
from framework.flask import secure_filename, redirect, send_file
from framework.exceptions import HTTPError
from website.addons.dataverse.client import connect, delete_file, upload_file, \
    get_file, get_file_by_id

from website.project.decorators import must_have_permission
from website.project.decorators import must_be_contributor_or_public
from website.project.decorators import must_not_be_registration
from website.project.decorators import must_have_addon
from website.project.views.node import _view_project
from website.project.views.file import get_cache_content
from website.util import rubeus
from website.addons.dataverse.model import DataverseFile
from website.addons.dataverse.settings import HOST
from website.addons.base.views import check_file_guid

import httplib as http

logger = logging.getLogger(__name__)

session = requests.Session()

@must_be_contributor_or_public
@must_have_addon('dataverse', 'node')
def dataverse_download_file(**kwargs):

    file_id = kwargs.get('path')
    if file_id is None:
        raise HTTPError(http.NOT_FOUND)

    return redirect('http://{0}/dvn/FileDownload/?fileId={1}'.format(HOST, file_id))


@must_be_contributor_or_public
@must_have_addon('dataverse', 'node')
def dataverse_download_file_proxy(**kwargs):

    file_id = kwargs.get('path')
    if file_id is None:
        raise HTTPError(http.NOT_FOUND)

    content, filename = scrape_dataverse(file_id)

    # Build response
    resp = make_response(content)
    resp.headers['Content-Disposition'] = 'attachment; filename={0}'.format(
        file_id
    )

    resp.headers['Content-Type'] = 'application/octet-stream'

    return resp


# TODO: Remove unnecessary API calls
@must_be_contributor_or_public
@must_have_addon('dataverse', 'node')
def dataverse_view_file(**kwargs):

    auth = kwargs['auth']
    node = kwargs['node'] or kwargs['project']
    node_settings = kwargs['node_addon']

    file_id = kwargs.get('path')
    if file_id is None:
        raise HTTPError(http.NOT_FOUND)

    # lazily create a file GUID record
    file_obj, created = DataverseFile.get_or_create(node=node, path=file_id)

    redirect_url = check_file_guid(file_obj)
    if redirect_url:
        return redirect(redirect_url)

    # Get or create rendered file
    cache_file = '{0}.html'.format(file_id)
    rendered = get_cache_content(node_settings, cache_file)
    filename = None

    if rendered is None:
        data, filename = scrape_dataverse(file_id)
        _, ext = os.path.splitext(filename)
        download_url = node.api_url_for(
            'dataverse_download_file_proxy', path=file_id
        )
        rendered = get_cache_content(
            node_settings, cache_file, start_render=True,
            file_path=file_id + ext, file_content=data,
            download_path=download_url,
        )

    rv = {
        'file_name': filename or scrape_filename(file_id),
        'rendered': rendered,
        'render_url': node.api_url_for('dataverse_get_rendered_file',
                                       path=file_id),
        'download_url': node.api_url_for('dataverse_download_file',
                                         path=file_id),
    }
    rv.update(_view_project(node, auth))
    return rv


@must_have_permission('write')
@must_not_be_registration
@must_have_addon('dataverse', 'node')
def dataverse_upload_file(**kwargs):

    node = kwargs['node'] or kwargs['project']
    auth = kwargs['auth']
    node_settings = kwargs['node_addon']

    now = datetime.datetime.utcnow()

    can_edit = node.can_edit(auth) and not node.is_registration
    can_view = node.can_view(auth)

    connection = connect(
        node_settings.dataverse_username,
        node_settings.dataverse_password
    )

    dataverse = connection.get_dataverse(node_settings.dataverse_alias)
    study = dataverse.get_study_by_hdl(node_settings.study_hdl)

    upload = request.files.get('file')
    filename = secure_filename(upload.filename)

    # Todo: Allow renaming
    if get_file(study, filename) is not None:
        raise HTTPError(
            http.BAD_REQUEST,
            message='This study already contains a file with that name'
        )

    content = upload.read()

    upload_file(study, filename, content)
    file_id = get_file(study, filename).id

    if file_id is None:
        raise HTTPError(http.BAD_REQUEST)

    node.add_log(
        action='dataverse_file_added',
        params={
            'project': node.parent_id,
            'node': node._primary_key,
            'filename': filename,
            'path': node.web_url_for('dataverse_view_file', path=file_id),
            'dataverse': {
                'dataverse': dataverse.title,
                'study': study.title,
            }
        },
        auth=auth,
        log_date=now,
    )

    info = {
        'addon': 'dataverse',
        'name': filename,
        'size': [
            len(content),
            rubeus.format_filesize(len(content))
        ],
        'kind': 'file',
        'urls': {
                'view': node.web_url_for('dataverse_view_file',
                                         path=file_id),
                'download': node.api_url_for('dataverse_download_file',
                                             path=file_id),
                'delete': node.api_url_for('dataverse_delete_file',
                                           path=file_id),
        },
        'permissions': {
            'view': can_view,
            'edit': can_edit,
        },
    }

    return info, 201



@must_have_permission('write')
@must_not_be_registration
@must_have_addon('dataverse', 'node')
def dataverse_delete_file(**kwargs):

    node = kwargs['node'] or kwargs['project']
    auth = kwargs['auth']
    node_settings = kwargs['node_addon']

    now = datetime.datetime.utcnow()

    file_id = kwargs.get('path')
    if file_id is None:
        raise HTTPError(http.NOT_FOUND)

    connection = connect(
        node_settings.dataverse_username,
        node_settings.dataverse_password
    )

    dataverse = connection.get_dataverse(node_settings.dataverse_alias)
    study = dataverse.get_study_by_hdl(node_settings.study_hdl)
    file = get_file_by_id(study, file_id)

    delete_file(file)

    # Check if file was deleted
    if get_file_by_id(study, file_id) is not None:
        raise HTTPError(http.BAD_REQUEST)

    node.add_log(
        action='dataverse_file_removed',
        params={
            'project': node.parent_id,
            'node': node._primary_key,
            'filename': file.name,
            'dataverse': {
                'dataverse': dataverse.title,
                'study': study.title,
            }
        },
        auth=auth,
        log_date=now,
    )

    return {}


@must_be_contributor_or_public
@must_have_addon('dataverse', 'node')
def dataverse_get_rendered_file(**kwargs):
    """

    """
    node_settings = kwargs['node_addon']
    file_id = kwargs['path']

    cache_file = '{0}.html'.format(file_id)
    return get_cache_content(node_settings, cache_file)


def scrape_dataverse(file_id):

    # Go to file url
    url = 'http://{0}/dvn/FileDownload/?fileId={1}'.format(HOST, file_id)
    response = session.get(url)

    # Agree to terms if necessary
    if '<title>Account Terms of Use -' in response.content:

        parsed = BeautifulSoup(response.content)
        view_state = parsed.find(id='javax.faces.ViewState').attrs.get('value')
        data = {
            'form1':'form1',
            'javax.faces.ViewState': view_state,
            'form1:termsAccepted':'on',
            'form1:termsButton':'Continue',
        }
        terms_url = 'http://{0}/dvn/faces/study/TermsOfUsePage.xhtml'.format(HOST)
        session.post(terms_url, data=data)
        response = session.get(url)

    filename = response.headers['content-disposition'].split('"')[1]

    # return file and name
    return response.content, filename


def scrape_filename(file_id):

    # Go to file url
    url = 'http://{0}/dvn/FileDownload/?fileId={1}'.format(HOST, file_id)
    headers = session.head(url).headers

    # Agree to terms if necessary
    if 'content-disposition' not in headers.keys():

        response = session.get(url)
        parsed = BeautifulSoup(response.content)
        view_state = parsed.find(id='javax.faces.ViewState').attrs.get('value')
        data = {
            'form1':'form1',
            'javax.faces.ViewState': view_state,
            'form1:termsAccepted':'on',
            'form1:termsButton':'Continue',
        }
        terms_url = 'http://{0}/dvn/faces/study/TermsOfUsePage.xhtml'.format(HOST)
        session.post(terms_url, data=data)
        headers = session.head(url).headers

    # return file and name
    return headers['content-disposition'].split('"')[1]
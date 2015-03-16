"""Views fo the node settings page."""
# -*- coding: utf-8 -*-
import os
import httplib as http

from flask import request
from box.client import BoxClientException
from urllib3.exceptions import MaxRetryError

from framework.exceptions import HTTPError

from website.util import permissions
from website.project.decorators import (
    must_have_addon, must_be_addon_authorizer,
    must_have_permission, must_not_be_registration,
)

#from website.addons.box.client import get_node_client
from website.addons.box.utils import (
    serialize_settings, serialize_urls
)


@must_have_addon('box', 'node')
@must_have_permission(permissions.WRITE)
def box_get_config(node_addon, auth, **kwargs):
    """API that returns the serialized node settings."""
    return {
        'result': serialize_settings(node_addon, auth.user),
    }


@must_not_be_registration
@must_have_addon('box', 'user')
@must_have_addon('box', 'node')
@must_be_addon_authorizer('box')
@must_have_permission(permissions.WRITE)
def box_set_config(node_addon, user_addon, auth, **kwargs):
    """View for changing a node's linked box folder."""
    folder = request.json.get('selected')

    uid = folder['id']
    path = folder['path']

    node_addon.set_folder(uid, auth=auth)

    return {
        'result': {
            'folder': {
                'name': path.replace('All Files', '') if path != 'All Files' else '/ (Full Box)',
                'path': path,
            },
            'urls': serialize_urls(node_addon),
        },
        'message': 'Successfully updated settings.',
    }


@must_have_addon('box', 'user')
@must_have_addon('box', 'node')
@must_have_permission(permissions.WRITE)
def box_add_user_auth(auth, node_addon, user_addon, **kwargs):
    """Import box credentials from the currently logged-in user to a node.
    """
    node_addon.set_user_auth(user_addon)
    node_addon.save()

    return {
        'result': serialize_settings(node_addon, auth.user),
        'message': 'Successfully imported access token from profile.',
    }


@must_not_be_registration
@must_have_addon('box', 'node')
@must_have_permission(permissions.WRITE)
def box_remove_user_auth(auth, node_addon, **kwargs):
    node_addon.deauthorize(auth=auth)
    node_addon.save()


@must_have_addon('box', 'user')
@must_have_addon('box', 'node')
@must_have_permission(permissions.WRITE)
def box_get_share_emails(auth, user_addon, node_addon, **kwargs):
    """Return a list of emails of the contributors on a project.

    The current user MUST be the user who authenticated Box for the node.
    """
    if not node_addon.user_settings:
        raise HTTPError(http.BAD_REQUEST)
    # Current user must be the user who authorized the addon
    if node_addon.user_settings.owner != auth.user:
        raise HTTPError(http.FORBIDDEN)

    return {
        'result': {
            'emails': [
                contrib.username
                for contrib in node_addon.owner.contributors
                if contrib != auth.user
            ],
        }
    }


@must_have_addon('box', 'node')
@must_be_addon_authorizer('box')
def box_folder_list(node_addon, **kwargs):
    """Returns a list of folders in Box"""
    if not node_addon.has_auth:
        raise HTTPError(http.FORBIDDEN)

    node = node_addon.owner
    folder_id = request.args.get('folderId')

    if folder_id is None:
        return [{
            'id': '0',
            'path': 'All Files',
            'addon': 'box',
            'kind': 'folder',
            'name': '/ (Full Box)',
            'urls': {
                'folders': node.api_url_for('box_list_folders', folderId=0),
            }
        }]

    try:
        client = node_addon.user_addon.oauth_settings.get_client  # get_node_client(node)
    except BoxClientException:
        raise HTTPError(http.FORBIDDEN)

    try:
        metadata = client.get_folder(folder_id)
    except BoxClientException:
        raise HTTPError(http.NOT_FOUND)
    except MaxRetryError:
        raise HTTPError(http.BAD_REQUEST)

    # Raise error if folder was deleted
    if metadata.get('is_deleted'):
        raise HTTPError(http.NOT_FOUND)

    folder_path = '/'.join(
        [
            x['name']
            for x in metadata['path_collection']['entries']
        ] + [metadata['name']]
    )

    return [
        {
            'addon': 'box',
            'kind': 'folder',
            'id': item['id'],
            'name': item['name'],
            'path': os.path.join(folder_path, item['name']),
            'urls': {
                'folders': node.api_url_for('box_list_folders', folderId=item['id']),
            }
        }
        for item in metadata['item_collection']['entries']
        if item['type'] == 'folder'
    ]

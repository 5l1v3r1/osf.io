from rest_framework import generics, permissions as drf_permissions

from website.models import NodeLog

from framework.auth.oauth_scopes import CoreScopes

from api.base.utils import get_object_or_error
from api.base import permissions as base_permissions
from api.logs.serializers import NodeLogSerializer
from api.base.views import JSONAPIBaseView


class NodeLogDetail(JSONAPIBaseView, generics.RetrieveAPIView):
    """Details about a given log. *Read-only*.

     On the front end, logs show record and show actions done on the OSF. The complete list of loggable actions (in the format {identifier}: {description}) is as follows:

    * 'project_created': A Node is created
    * 'project_registered': A Node is registered
    * 'project_deleted': A Node is deleted
    * 'created_from': A Node is created using an existing Node as a template
    * 'pointer_created': A Pointer is created
    * 'pointer_forked': A Pointer is forked
    * 'pointer_removed': A Pointer is removed
    ---
    * 'made_public': A Node is made public
    * 'made_private': A Node is made private
    * 'tag_added': A tag is added to a Node
    * 'tag_removed': A tag is removed from a Node
    * 'edit_title': A Node's title is changed
    * 'edit_description': A Node's description is changed
    * 'updated_fields': One or more of a Node's fields are changed
    * 'external_ids_added': An external identifier is added to a Node (e.g. DOI, ARK)
    ---
    * 'contributor_added': A Contributor is added to a Node
    * 'contributor_removed': A Contributor is removed from a Node
    * 'contributors_reordered': A Contributor's position is a Node's biliography is changed
    * 'permissions_update': A Contributor's permissions on a Node are changed
    * 'made_contributor_visible': A Contributor is made bibliographically visible on a Node
    * 'made_contributor_invisible': A Contributor is made bibliographically invisible on a Node
    ---
    * 'wiki_updated': A Node's wiki is updated
    * 'wiki_deleted': A Node's wiki is deleted
    * 'wiki_renamed': A Node's wiki is renamed
    * 'made_wiki_public': A Node's wiki is made public
    * 'made_wiki_private': A Node's wiki is made private
    ---
    * 'addon_added': An add-on is linked to a Node
    * 'addon_removed': An add-on is unlinked from a Node
    * 'addon_file_moved': A File in a Node's linked add-on is moved
    * 'addon_file_copied': A File in a Node's linked add-on is copied
    * 'addon_file_renamed': A File in a Node's linked add-on is renamed
    * 'folder_created': A Folder is created in a Node's linked add-on
    * 'file_added': A File is added to a Node's linked add-on
    * 'file_updated': A File is updated on a Node's linked add-on
    * 'file_removed': A File is removed from a Node's linked add-on
    * 'file_restored': A File is restored in a Node's linked add-on
    ---
    * 'comment_added': A Comment is added to some item
    * 'comment_removed': A Comment is removed from some item
    * 'comment_updated': A Comment is updated on some item
    ---
    * 'embargo_initiated': An embargoed Registration is proposed on a Node
    * 'embargo_approved': A proposed Embargo of a Node is approved
    * 'embargo_cancelled': A proposed Embargo of a Node is cancelled
    * 'embargo_completed': A proposed Embargo of a Node is completed
    * 'retraction_initiated': A Retraction of a Registration is proposed
    * 'retraction_approved': A Retraction of a Registration is approved
    * 'retraction_cancelled': A Retraction of a Registration is cancelled
    * 'registration_initiated': A Registration of a Node is proposed
    * 'registration_approved': A proposed Registration is approved
    * 'registration_cancelled': A proposed Registration is cancelled
    ---
    * 'node_created': A Node is created (_deprecated_)
    * 'node_forked': A Node is forked (_deprecated_)
    * 'node_removed': A Node is dele (_deprecated_)

   ##Log Attributes

    <!--- Copied Attributes from LogList -->

    OSF Log entities have the "logs" `type`.

        name           type                   description
        ----------------------------------------------------------------------------
        date           iso8601 timestamp      timestamp of Log creation
        action         string                 Log action (see list above)

    ##Relationships

    ###Node

    The node this log belongs to.

    ###User

    The user who performed the logged action.

    ##Links

    See the [JSON-API spec regarding pagination](http://jsonapi.org/format/1.0/#fetching-pagination).

    ##Actions

    ##Query Params

    <!--- Copied Query Params from LogList -->

    Logs may be filtered by their `action` and `date`.

    #This Request/Response

    """
    permission_classes = (
        drf_permissions.IsAuthenticatedOrReadOnly,
        base_permissions.TokenHasScope,
    )

    required_read_scopes = [CoreScopes.NODE_BASE_READ]
    required_write_scopes = [CoreScopes.NODE_BASE_WRITE]

    serializer_class = NodeLogSerializer
    view_category = 'logs'
    view_name = 'log-detail'

    # overrides RetrieveUpdateDestroyAPIView
    def get_object(self):
        log = get_object_or_error(
            NodeLog,
            self.kwargs['log_id'],
            display_name='log'
        )
        # May raise a permission denied
        self.check_object_permissions(self.request, log)
        return log

    # overrides RetrieveUpdateDestroyAPIView
    def perform_destroy(self, instance):
        pass

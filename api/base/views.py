from django.core.urlresolvers import resolve, reverse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics

from api.base.utils import absolute_reverse
from api.users.serializers import UserSerializer

class JSONAPIBaseView(generics.GenericAPIView):

    def _get_include_partial(self, field_name):
        """Create a partial function to fetch the values of an included field. A basic
        example is to include a Node's children in a single response.

        :param str field_name: Name of field of the view's serializer_class to load
        results for
        :return function (Request, type) -> dict | list:
        """
        include_field = self.serializer_class._declared_fields[field_name]
        def partial(request, item, **kwargs):
            include_value = getattr(item, include_field.lookup_field, None)
            view_kwargs = {include_field.lookup_url_kwarg: include_value}
            view, view_args, view_kwargs = resolve(reverse(include_field.view_name, kwargs=view_kwargs))
            view_kwargs['request'] = request
            view_kwargs.update(kwargs)
            response = view(*view_args, **view_kwargs)
            return response.data.get('data')
        return partial

    def get_serializer_context(self):
        """Inject request into the serializer context. Additionally, inject partial functions
        (request, object -> included items) if the query string contains includes, and this
        is the topmost call to this method (the include partials call view functions which has
        the potential to create infinite recursion hence the inclusion of the no_includes
        view kwarg to prevent this).
        """
        context = super(JSONAPIBaseView, self).get_serializer_context()
        if self.kwargs.get('no_includes', False):
            return context
        includes = self.request.query_params.getlist('include')
        includes_partials = {}
        for include in includes:
            include_field = self.serializer_class._declared_fields.get(include)
            if include_field and getattr(include_field, 'includable', False):
                includes_partials[include] = self._get_include_partial(include)
        context.update({
            'include': includes_partials
        })
        return context

@api_view(('GET',))
def root(request, format=None):
    """
        Welcome to the V2 Open Science Framework API. With this API you can programatically access users,
        projects, components, and files from the [Open Science Framework](https://osf.io/). The Open Science
        Framework (OSF) is a free, open-source service maintained by the [Center for Open Science](http://cos.io/).


        The OSF stores, documents, and archives study designs, materials, data, manuscripts, or anything else associated
        with your research during the research process. Every project and file on the OSF has a permanent unique
        identifier, and every registration (a permanent, time-stamped version of your projects and files) can be assigned
         a DOI/ARK. You can use the OSF to measure your impact by monitoring the traffic to projects and files you make
         public. With the OSF you have full control of what parts of your research are public and what remains private.

        Beta notice: This API is currently a beta service.  You are encouraged to use the API and will receive support
        when doing so, however, while the API remains in beta status, it may change without notice as a result of
        product updates. The temporary beta status of the API will remain in place while it matures. In a future
        release, the beta status will be removed, at which point we will provide details on how long we will support
        the API V2 and under what circumstances it might change.

        ##General API Usage
        Each endpoint will have its own documentation, but there are some general principles.

        ###Filtering
        Collections can be filtered by adding a query parameter in the form:

            filter[<fieldname>]=<matching information>
        For example, if you were trying to find [Lise Meitner](http://en.wikipedia.org/wiki/Lise_Meitner):

            /users?filter[fullname]=meitn
        You can filter on multiple fields, or the same field in different ways, by &-ing the query parameters together.

            /users?filter[fullname]=lise&filter[family_name]=mei
        ###Links
        Responses will generally have associated links which are helpers to keep you from having to construct URLs in
        your code or by hand. If you know the route to a high-level resource, you can go to that route. For example:

            /nodes/<node_id>

        is a good route to create rather than going to /nodes/ and navigating by id filtering. However, if you are
        creating something that crawls the structure of a node going to the child node or gathering children,
        contributors, and similar related resources, then take the link from the object you\'re crawling rather than
        constructing the link yourself.

        In general, links include:

        1. "Related" links, which will give detailed information on individual items or a collection of related resources;
        2. "Self" links, which are used for general REST operations (POST, DELETE, and so on);
        3. Pagination links such as "next", "prev", "first", and "last". Pagination links are great for navigating long
        lists of information.

        Some routes may have extra rules for links, especially if those links work with external services. Collections
        may have counts with them to indicate how many items are in that collection.
    """
    if request.user and not request.user.is_anonymous():
        user = request.user
        current_user = UserSerializer(user, context={'request': request}).data
    else:
        current_user = None

    return Response({
        'meta': {
            'message': 'Welcome to the OSF API.',
            'version': request.version,
            'current_user': current_user,
        },
        'links': {
            'nodes': absolute_reverse('nodes:node-list'),
            'users': absolute_reverse('users:user-list'),
        }
    })

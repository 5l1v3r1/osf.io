from django.core.exceptions import ImproperlyConfigured
from rest_framework import exceptions, permissions

from framework.auth import oauth_scopes

# Implementation built on django-oauth-toolkit, but  with more granular control over read+write permissions
#   https://github.com/evonove/django-oauth-toolkit/blob/d45431ea0bf64fd31e16f429db1e902dbf30e3a8/oauth2_provider/ext/rest_framework/permissions.py#L15
class TokenHasScope(permissions.BasePermission):
    """
    The provided access token must include all of the base scopes listed in the view (exactly match for names)

    Requires the user to define `read_scopes` and `write_scopes` attributes based on names of publicly defined composed
        scopes
    """
    def has_object_permission(self, request, view, obj):
        # FIXME: Implement
        return True

    def has_permission(self, request, view):
        token = request.auth

        if token is None:
            # Assumption: user authenticated via non-oauth means, so don't check token permissions.
            return True

        required_scopes = self._get_scopes(request, view)

        # Scopes are returned as a space-delimited list in the token
        allowed_scopes = token.scopes

        try:
            normalized_scopes = self._normalize_scopes(allowed_scopes)
        except KeyError:
            # This should never fire: it implies that CAS issued a scope name not in the master list of scopes
            raise exceptions.APIException("OAuth2 token specifies unrecognized scope.")

        return required_scopes.issubset(normalized_scopes)

    def _get_scopes(self, request, view):
        """Get the list of scopes appropriate to the request (read or read + write)"""
        try:
            read_scopes = set(view.required_read_scopes)
        except AttributeError:
            raise ImproperlyConfigured('TokenHasScope requires the view to define the required_read_scopes attribute')

        if request.method in permissions.SAFE_METHODS:
            return read_scopes
        else:
            # A write operation implicitly also requires access to read scopes

            try:
                write_scopes = set(view.required_write_scopes)
            except AttributeError:
                raise ImproperlyConfigured('TokenHasScope requires the view to define the required_write_scopes attribute')

            return read_scopes | write_scopes

    def _normalize_scopes(self, scopes):
        """
        Given a list of public-facing scope names from a CAS token, return the list of internal scopes

        This is useful for converting a single broad scope into the small constituent parts
        """
        all_scopes = set()
        for sc in scopes:
            all_scopes |= oauth_scopes.public_scopes[sc]
        return all_scopes

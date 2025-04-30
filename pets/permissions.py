from rest_framework.permissions import BasePermission


class HasAPIKey(BasePermission):
    """
    Used IN CONJUNCTION WITH APIKeyAuthentication.
    """

    message = "A valid API key is required in the X-API-KEY header."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

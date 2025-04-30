from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get("X-API-KEY")

        if not api_key:
            return None

        expected_key = getattr(settings, "API_KEY", None)

        if not expected_key or api_key != expected_key:
            raise AuthenticationFailed("Invalid or missing API Key.")

        # If the key is valid, return a simple user object indicating success.
        class APIUser:
            is_authenticated = True

        return APIUser(), api_key

    def authenticate_header(self, request):
        return "X-API-KEY"

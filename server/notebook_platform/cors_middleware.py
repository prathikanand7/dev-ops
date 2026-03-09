from django.http import HttpResponse
from django.conf import settings


class DevCorsMiddleware:
    """Minimal CORS middleware for local dev frontend -> backend API calls."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get('Origin', '')
        is_allowed = origin in getattr(settings, 'CORS_ALLOWED_ORIGINS', [])

        if request.method == 'OPTIONS' and is_allowed:
            response = HttpResponse(status=200)
        else:
            response = self.get_response(request)

        if is_allowed:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-CSRFToken'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Vary'] = 'Origin'

        return response

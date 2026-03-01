import secrets
from django.conf import settings
from rest_framework.permissions import BasePermission

class IsKubernetesWorker(BasePermission):
    """
    Custom permission to only allow Kubernetes workers with the shared secret 
    to hit the webhook endpoints.
    """
    def has_permission(self, request, view):
        provided_token = request.headers.get('X-Worker-Token')
        expected_token = getattr(settings, 'WORKER_WEBHOOK_SECRET', None)
        
        # Fail securely if the server itself is secret is missing
        if not expected_token:
            return False
            
        # Reject if the worker didn't provide a token
        if not provided_token:
            return False
            
        # Compare the tokens in constant time
        return secrets.compare_digest(provided_token, expected_token)
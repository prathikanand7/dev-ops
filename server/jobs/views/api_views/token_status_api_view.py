from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, inline_serializer

class TokenStatusAPIView(APIView):
    """
    API endpoint to check if a user has an active API token.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Check API Token Status",
        description="Returns a boolean indicating if the current user has an active API token.",
        responses={
            200: inline_serializer(
                name='TokenStatusResponse',
                fields={'has_token': serializers.BooleanField()}
            )
        }
    )
    def get(self, request):
        has_token = Token.objects.filter(user=request.user).exists()
        return Response({'has_token': has_token})
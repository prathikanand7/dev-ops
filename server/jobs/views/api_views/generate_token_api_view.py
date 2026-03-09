from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, inline_serializer

class GenerateTokenAPIView(APIView):
    """
    API endpoint to generate a new API token for the user, invalidating any existing token.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Generate API Token",
        description="Invalidates any existing token and generates a new one for the current user.",
        responses={
            201: inline_serializer(
                name='TokenGenerateResponse',
                fields={'token': serializers.CharField()}
            )
        }
    )
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        new_token = Token.objects.create(user=request.user)
        return Response({'token': new_token.key}, status=status.HTTP_201_CREATED)
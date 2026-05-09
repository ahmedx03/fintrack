import logging
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer, UserSerializer, UpdateProfileSerializer
from .models import User
from .throttles import LoginRateThrottle, RegisterRateThrottle

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (RegisterRateThrottle,)


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/me/   — return current user's profile
    PATCH /api/auth/me/  — update email and/or password
    """
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names  = ['get', 'patch']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UpdateProfileSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """
    Blacklists the submitted refresh token, invalidating it server-side.
    The client must also delete its stored tokens.

    POST /api/auth/logout/
    Body: { "refresh": "<refresh_token>" }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            # Already blacklisted or invalid — treat as a successful logout
            return Response(status=status.HTTP_205_RESET_CONTENT)

from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"


class LoginView(TokenObtainPairView):
    """Same as simplejwt's view, but rate limited against brute force."""

    throttle_scope = "auth"

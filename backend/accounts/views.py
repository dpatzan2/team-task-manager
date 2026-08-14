from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer


def set_auth_cookies(response, tokens):
    options = {"httponly": True, "secure": not settings.DEBUG, "samesite": "Strict", "path": "/api/"}
    response.set_cookie("access", tokens["access"], max_age=300, **options)
    if tokens.get("refresh"):
        response.set_cookie("refresh", tokens["refresh"], max_age=86400, **options)
    return response


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"


class LoginView(TokenObtainPairView):
    """Same as simplejwt's view, but rate limited against brute force."""

    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return set_auth_cookies(Response({}), response.data)


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data={"refresh": request.COOKIES.get("refresh")})
        serializer.is_valid(raise_exception=True)
        return set_auth_cookies(Response({}), serializer.validated_data)


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        response = Response(status=204)
        response.delete_cookie("access", path="/api/")
        response.delete_cookie("refresh", path="/api/")
        return response


class SessionView(APIView):
    def get(self, request):
        return Response({"username": request.user.username})

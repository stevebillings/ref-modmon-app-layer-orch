"""
Authentication views for login, logout, and session management.
"""

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from infrastructure.django_app.user_context_adapter import build_user_context


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request: Request) -> Response:
    """
    Authenticate user and create session.

    POST /api/auth/login/
    Body: {"username": "...", "password": "..."}
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)

    if user is None:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    login(request, user)

    try:
        user_context = build_user_context(user)
    except Exception:
        return Response(
            {"error": "User profile not found"},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        {
            "user": {
                "id": str(user_context.user_id),
                "username": user_context.username,
                "role": user_context.role.value,
            }
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request: Request) -> Response:
    """
    End user session.

    POST /api/auth/logout/
    """
    logout(request)
    return Response({"message": "Logged out successfully"})


@api_view(["GET"])
@permission_classes([AllowAny])
def session_view(request: Request) -> Response:
    """
    Get current session status and CSRF token.

    GET /api/auth/session/

    Used by frontend to check if user is logged in on app load.
    """
    csrf_token = get_token(request)

    if request.user.is_authenticated:
        try:
            user_context = build_user_context(request.user)
            return Response(
                {
                    "authenticated": True,
                    "user": {
                        "id": str(user_context.user_id),
                        "username": user_context.username,
                        "role": user_context.role.value,
                    },
                    "csrf_token": csrf_token,
                }
            )
        except Exception:
            # User exists but no profile - log them out
            logout(request)

    return Response(
        {
            "authenticated": False,
            "csrf_token": csrf_token,
        }
    )

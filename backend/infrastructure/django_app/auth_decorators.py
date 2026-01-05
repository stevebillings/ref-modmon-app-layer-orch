"""
Authentication decorators for Django views.

Provides decorators that extract UserContext from authenticated requests
and inject it into view functions.
"""

from functools import wraps
from typing import Any, Callable, cast

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from infrastructure.django_app.user_context_adapter import build_user_context


def require_auth(view_func: Callable) -> Callable:
    """
    Decorator that requires authentication and injects UserContext.

    Extracts UserContext from the authenticated request and adds it
    as a keyword argument to the view function.

    Usage:
        @api_view(["GET"])
        @require_auth
        def my_view(request, user_context: UserContext):
            # user_context is available here
            pass
    """

    @wraps(view_func)
    def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user_context = build_user_context(request.user)
        except Exception:
            return Response(
                {"error": "User profile not found"},
                status=status.HTTP_403_FORBIDDEN,
            )

        kwargs["user_context"] = user_context
        return cast(Response, view_func(request, *args, **kwargs))

    return wrapper

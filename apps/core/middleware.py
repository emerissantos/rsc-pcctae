import uuid

from .context import (
    reset_current_user,
    reset_request_id,
    set_current_user,
    set_request_id,
)


class RequestCorrelationMiddleware:
    header_name = "HTTP_X_REQUEST_ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.META.get(self.header_name) or str(uuid.uuid4())
        request.request_id = request_id
        token = set_request_id(request_id)
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            return response
        finally:
            reset_request_id(token)


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = (
            request.user
            if getattr(request, "user", None) and request.user.is_authenticated
            else None
        )
        token = set_current_user(user)
        try:
            return self.get_response(request)
        finally:
            reset_current_user(token)

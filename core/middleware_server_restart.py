from django.conf import settings
from django.contrib.auth import logout

class DevLogoutOnRestartMiddleware:
    """
    DEV-only: logs out users if server instance ID changes.
    Prevents weird "back button shows old dashboard" behaviour during development.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only run in DEBUG
        if not getattr(settings, "DEBUG", False):
            return self.get_response(request)

        # ✅ request.user may not exist depending on middleware order
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return self.get_response(request)

        session = getattr(request, "session", None)
        if session is None:
            return self.get_response(request)

        server_id = getattr(settings, "DEV_SERVER_INSTANCE_ID", "dev-1")
        last_id = session.get("_dev_server_id")

        if last_id and last_id != server_id:
            logout(request)
            session.flush()
        session["_dev_server_id"] = server_id

        return self.get_response(request)
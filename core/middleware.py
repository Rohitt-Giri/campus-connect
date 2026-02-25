# core/middleware.py
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers


AUTH_PAGES = (
    "/accounts/login/",
    "/accounts/register/",
    "/accounts/pending/",
    "/accounts/password-reset/",
    "/accounts/password-reset/done/",
    "/accounts/reset/",       # includes /reset/<uidb64>/<token>/
    "/accounts/reset/done/",
)

ROLE_DASHBOARDS = {
    "STUDENT": "/student/dashboard/",
    "STAFF": "/staff/dashboard/",
    "ADMIN": "/accounts/admin-dashboard/",
}


def _dashboard_for(user):
    if getattr(user, "is_superuser", False):
        return ROLE_DASHBOARDS["ADMIN"]
    role = getattr(user, "role", None)
    return ROLE_DASHBOARDS.get(role, "/")


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


class NoCacheAndAuthRedirectMiddleware:
    """
    Production-friendly:
    1) Add no-cache headers for authenticated pages (fix back button after logout)
    2) Redirect authenticated users away from auth pages to their dashboards
    3) Prevent role URL mixing (student vs staff vs admin)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        path = request.path or "/"

        # If logged in:
        if user and getattr(user, "is_authenticated", False):

            # ✅ stop logged-in user from seeing login/register/reset pages
            if any(path.startswith(p) for p in AUTH_PAGES):
                return redirect(_dashboard_for(user))

            # ✅ role guard (avoid student/staff mixing by URL)
            if not getattr(user, "is_superuser", False):
                role = getattr(user, "role", None)

                if role == "STUDENT":
                    if path.startswith("/staff/") or path.startswith("/accounts/admin"):
                        return redirect(_dashboard_for(user))

                if role == "STAFF":
                    if path.startswith("/student/"):
                        return redirect(_dashboard_for(user))

        response = self.get_response(request)

        # ✅ prevent browser caching for logged-in pages
        if user and getattr(user, "is_authenticated", False):
            add_never_cache_headers(response)

        return response
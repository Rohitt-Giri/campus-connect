from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy

def staff_required(view_func):
    """
    Allows only users with role=STAFF (your custom user field).
    Adjust if your field name is different.
    """
    return user_passes_test(
        lambda u: u.is_authenticated and getattr(u, "role", None) == "STAFF",
        login_url="accounts:login"
    )(view_func)

def admin_required(view_func):
    """
    Allow only:
    - Django superuser (is_superuser)
    OR
    - users with role == ADMIN (custom user role)
    """
    return user_passes_test(
        lambda u: u.is_authenticated and (u.is_superuser or getattr(u, "role", None) == "ADMIN"),
        login_url=reverse_lazy("accounts:login")
    )(view_func)
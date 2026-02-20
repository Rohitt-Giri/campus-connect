from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages

from .models import User


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        # Allow superuser always
        if getattr(request.user, "is_superuser", False):
            return view_func(request, *args, **kwargs)

        # Must be approved + role admin
        if getattr(request.user, "role", None) != User.Role.ADMIN:
            return HttpResponseForbidden("Admin only")

        if not getattr(request.user, "is_approved", False):
            messages.error(request, "Your admin account is not approved.")
            return redirect("accounts:login")

        if not getattr(request.user, "is_active", True):
            return HttpResponseForbidden("Account inactive")

        return view_func(request, *args, **kwargs)

    return _wrapped

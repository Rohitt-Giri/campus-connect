from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from .models import User
from .decorators import admin_required


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created. Please wait for admin approval.")
            return redirect("accounts:pending")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def pending_approval_view(request):
    return render(request, "accounts/pending_approval.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password.")
            return redirect("accounts:login")

        # Block deactivated users (rejected)
        if not user.is_active:
            messages.error(request, "Your account was deactivated. Please contact admin.")
            return redirect("accounts:login")

        # Approval gate for Student/Staff
        if user.role in [User.Role.STUDENT, User.Role.STAFF] and not user.is_approved:
            return redirect("accounts:pending")

        login(request, user)

        # Role-based redirect
        if user.is_superuser:
            return redirect("accounts:admin_dashboard")

        if user.role == User.Role.ADMIN:
            return redirect("accounts:admin_dashboard")

        if user.role == User.Role.STUDENT:
            return redirect("student:dashboard")

        if user.role == User.Role.STAFF:
            return redirect("staff:dashboard")

        messages.error(request, "User role not recognized.")
        return redirect("accounts:login")

    return render(request, "accounts/login.html")


@login_required
def post_login_redirect_view(request):
    user = request.user

    if user.is_superuser or user.role == User.Role.ADMIN:
        return redirect("accounts:admin_dashboard")

    if user.role == User.Role.STUDENT:
        return redirect("student:dashboard")

    if user.role == User.Role.STAFF:
        return redirect("staff:dashboard")

    return redirect("accounts:login")


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


# ---------------------------
# CUSTOM ADMIN DASHBOARD FLOW
# ---------------------------

@admin_required
def admin_dashboard_view(request):
    """
    Shows pending Student/Staff accounts + quick stats.
    """
    pending_users = User.objects.filter(
        role__in=[User.Role.STUDENT, User.Role.STAFF],
        is_approved=False,
        is_active=True
    ).order_by("-date_joined")

    stats = {
        "students_total": User.objects.filter(role=User.Role.STUDENT, is_active=True).count(),
        "staff_total": User.objects.filter(role=User.Role.STAFF, is_active=True).count(),
        "pending_total": pending_users.count(),
    }

    return render(
        request,
        "accounts/admin_dashboard.html",
        {"pending_users": pending_users, "stats": stats}
    )


@admin_required
@require_POST
def approve_user_view(request, user_id):
    """
    Approve Student/Staff: is_approved=True, keep active.
    """
    user = get_object_or_404(User, id=user_id)

    if user.role not in [User.Role.STUDENT, User.Role.STAFF]:
        messages.error(request, "Only Student/Staff accounts can be approved here.")
        return redirect("accounts:admin_dashboard")

    if not user.is_active:
        messages.error(request, "This account is deactivated. Reactivate it first if needed.")
        return redirect("accounts:admin_dashboard")

    user.is_approved = True
    user.save(update_fields=["is_approved"])

    messages.success(request, f"Approved: {user.username}")
    return redirect("accounts:admin_dashboard")


@admin_required
@require_POST
def reject_user_view(request, user_id):
    """
    Reject (Deactivate): is_active=False, is_approved=False.
    Keeps record in DB (Option B).
    """
    user = get_object_or_404(User, id=user_id)

    if user.role not in [User.Role.STUDENT, User.Role.STAFF]:
        messages.error(request, "Only Student/Staff accounts can be rejected here.")
        return redirect("accounts:admin_dashboard")

    user.is_active = False
    user.is_approved = False
    user.save(update_fields=["is_active", "is_approved"])

    messages.warning(request, f"Deactivated: {user.username}")
    return redirect("accounts:admin_dashboard")


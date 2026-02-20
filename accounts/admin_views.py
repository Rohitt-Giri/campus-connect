from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import admin_required
from .models import User

# Optional module imports (safe)
try:
    from events.models import Event, EventRegistration
except Exception:
    Event = None
    EventRegistration = None

try:
    from notices.models import Notice
except Exception:
    Notice = None

try:
    from payments.models import PaymentProof
except Exception:
    PaymentProof = None

try:
    from lostfound.models import ClaimRequest, LostFoundItem
except Exception:
    ClaimRequest = None
    LostFoundItem = None


@admin_required
def admin_dashboard_view(request):
    """
    Shows pending Student/Staff accounts + quick stats + module overview.
    """
    pending_users = User.objects.filter(
        role__in=[User.Role.STUDENT, User.Role.STAFF],
        is_approved=False,
        is_active=True
    ).order_by("-date_joined")

    # Base stats
    stats = {
        "students_total": User.objects.filter(role=User.Role.STUDENT, is_active=True).count(),
        "staff_total": User.objects.filter(role=User.Role.STAFF, is_active=True).count(),
        "pending_total": pending_users.count(),
    }

    # Module stats (safe)
    stats["events_total"] = Event.objects.count() if Event else 0
    stats["registrations_total"] = EventRegistration.objects.count() if EventRegistration else 0
    stats["notices_total"] = Notice.objects.filter(is_active=True).count() if Notice else 0
    stats["pending_payments"] = PaymentProof.objects.filter(status="pending").count() if PaymentProof else 0
    stats["pending_claims"] = ClaimRequest.objects.filter(status="pending").count() if ClaimRequest else 0
    stats["lostfound_items"] = LostFoundItem.objects.count() if LostFoundItem else 0

    return render(
        request,
        "accounts/admin_dashboard.html",
        {"pending_users": pending_users, "stats": stats}
    )


@admin_required
def approve_user_view(request, user_id):
    """
    Approve a Student/Staff account.
    """
    u = get_object_or_404(User, id=user_id)

    if u.role not in [User.Role.STUDENT, User.Role.STAFF]:
        messages.error(request, "Only Student/Staff accounts can be approved here.")
        return redirect("accounts:admin_dashboard")

    u.is_approved = True
    u.is_active = True
    u.save(update_fields=["is_approved", "is_active"])
    messages.success(request, f"Approved: {u.username} ✅")
    return redirect("accounts:admin_dashboard")


@admin_required
def reject_user_view(request, user_id):
    """
    Reject a Student/Staff account (deactivate).
    """
    u = get_object_or_404(User, id=user_id)

    if u.role not in [User.Role.STUDENT, User.Role.STAFF]:
        messages.error(request, "Only Student/Staff accounts can be rejected here.")
        return redirect("accounts:admin_dashboard")

    # safest: deactivate (don’t delete)
    u.is_active = False
    u.is_approved = False
    u.save(update_fields=["is_active", "is_approved"])
    messages.success(request, f"Rejected/Deactivated: {u.username} ❌")
    return redirect("accounts:admin_dashboard")


@admin_required
def change_role_view(request, user_id):
    """
    Change role for a user (Student/Staff/Admin).
    """
    u = get_object_or_404(User, id=user_id)

    if request.method != "POST":
        return redirect("accounts:admin_dashboard")

    new_role = (request.POST.get("role") or "").strip()

    valid = {User.Role.STUDENT, User.Role.STAFF, User.Role.ADMIN}
    if new_role not in valid:
        messages.error(request, "Invalid role.")
        return redirect("accounts:admin_dashboard")

    # Optional safety: don’t let admin demote themselves accidentally
    if u.id == request.user.id and new_role != User.Role.ADMIN:
        messages.error(request, "You cannot remove your own admin role.")
        return redirect("accounts:admin_dashboard")

    u.role = new_role
    # if admin sets role, ensure active (up to you)
    u.is_active = True
    u.save(update_fields=["role", "is_active"])

    messages.success(request, f"Role updated: {u.username} → {new_role}")
    return redirect("accounts:admin_dashboard")

@admin_required
def admin_users_view(request):
    """
    Full user management page for Admin.
    Shows ALL users with filters + search.
    """

    users = User.objects.all().order_by("-date_joined")

    # 🔎 Search
    q = (request.GET.get("q") or "").strip()
    if q:
        users = users.filter(username__icontains=q)

    # 🎯 Role filter
    role = request.GET.get("role")
    if role in [User.Role.STUDENT, User.Role.STAFF, User.Role.ADMIN]:
        users = users.filter(role=role)

    # ✅ Approved filter
    approved = request.GET.get("approved")
    if approved == "yes":
        users = users.filter(is_approved=True)
    elif approved == "no":
        users = users.filter(is_approved=False)

    return render(
        request,
        "accounts/admin_users.html",
        {
            "users": users,
            "q": q,
            "role": role,
            "approved": approved,
        }
    )

@admin_required
def toggle_active_view(request, user_id):
    """
    Admin can deactivate/reactivate any user.
    """

    u = get_object_or_404(User, id=user_id)

    if u.id == request.user.id:
        messages.error(request, "You cannot deactivate yourself.")
        return redirect("accounts:admin_users")

    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])

    state = "Activated" if u.is_active else "Deactivated"
    messages.success(request, f"{state}: {u.username}")

    return redirect("accounts:admin_users")
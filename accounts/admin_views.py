from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .models import User

# OPTIONAL apps (safe)
try:
    from events.models import Event, EventRegistration
except Exception:
    Event = None
    EventRegistration = None

try:
    from payments.models import PaymentProof
except Exception:
    PaymentProof = None

try:
    from lostfound.models import ClaimRequest, LostFoundItem
except Exception:
    ClaimRequest = None
    LostFoundItem = None

try:
    from notices.models import Notice
except Exception:
    Notice = None

try:
    from audit.models import AuditLog
except Exception:
    AuditLog = None

# Optional: email helper (only if you already have it)
try:
    from .email_utils import send_user_approved_email as send_approval_email
except Exception:
    send_approval_email = None


# ==========================================================
# ADMIN DASHBOARD (THIS IS WHAT YOUR URL USES ✅)
# ==========================================================
@never_cache
@admin_required
def admin_dashboard_view(request):
    now = timezone.now()

    # Pending Student/Staff approvals
    pending_users = User.objects.filter(
        role__in=[User.Role.STUDENT, User.Role.STAFF],
        is_approved=False,
        is_active=True
    ).order_by("-date_joined")

    students_total = User.objects.filter(role=User.Role.STUDENT, is_active=True).count()
    staff_total = User.objects.filter(role=User.Role.STAFF, is_active=True).count()

    # =========================
    # EVENTS COUNT (FIXED ✅)
    # - This is why you saw 17
    # - We count ONLY:
    #   is_active=True AND archived_at IS NULL AND status="published"
    # =========================
    events_total = 0
    upcoming_events_count = 0
    latest_events = []
    registrations_total = 0

    if Event:
        # ✅ the ONLY truth for dashboard
        events_qs = Event.objects.filter(
            is_active=True,
            archived_at__isnull=True,
            status="published",
        )

        events_total = events_qs.count()
        upcoming_events_count = events_qs.filter(start_datetime__gte=now).count()
        latest_events = events_qs.order_by("-created_at")[:5]

    if EventRegistration:
        registrations_total = EventRegistration.objects.count()

    # Notices
    notices_total = Notice.objects.filter(is_active=True).count() if Notice else 0

    # Payments
    pending_payments = approved_payments = rejected_payments = 0
    payments_pending = []
    if PaymentProof:
        pay_qs = PaymentProof.objects.select_related("registration__event", "registration__user")
        pending_payments = pay_qs.filter(status="pending").count()
        approved_payments = pay_qs.filter(status="approved").count()
        rejected_payments = pay_qs.filter(status="rejected").count()
        order_field = "-submitted_at" if hasattr(PaymentProof, "submitted_at") else "-id"
        payments_pending = pay_qs.filter(status="pending").order_by(order_field)[:5]

    # Lost & Found
    items_total = LostFoundItem.objects.count() if LostFoundItem else 0
    pending_claims = 0
    pending_claims_list = []
    if ClaimRequest:
        pending_claims = ClaimRequest.objects.filter(status="pending").count()
        order_field = "-created_at" if hasattr(ClaimRequest, "created_at") else "-id"
        pending_claims_list = ClaimRequest.objects.select_related("student", "item").filter(
            status="pending"
        ).order_by(order_field)[:5]

    # Recent logs
    recent_logs = AuditLog.objects.select_related("actor").order_by("-created_at")[:10] if AuditLog else []

    # ✅ DEBUG: this proves which file/view is running
    print("ADMIN_DASHBOARD_VIEW counts => published_active_events:", events_total)

    stats = {
        "students_total": students_total,
        "staff_total": staff_total,
        "pending_total": pending_users.count(),

        # ✅ this is what your template prints
        "events_total": events_total,

        "registrations_total": registrations_total,
        "notices_total": notices_total,

        "pending_payments": pending_payments,
        "pending_claims": pending_claims,
    }

    overview = {
        "upcoming_events_count": upcoming_events_count,
        "latest_events": latest_events,

        "payments_counts": {
            "pending": pending_payments,
            "approved": approved_payments,
            "rejected": rejected_payments,
        },
        "payments_pending": payments_pending,

        "lostfound_counts": {
            "items": items_total,
            "pending_claims": pending_claims,
        },
        "pending_claims": pending_claims_list,
    }

    return render(request, "accounts/admin_dashboard.html", {
        "pending_users": pending_users,
        "stats": stats,
        "overview": overview,
        "recent_logs": recent_logs,
        "unread_count": 0,
        "year": now.year,
    })


# ==========================================================
# ADMIN ACTIONS
# ==========================================================
@admin_required
@require_POST
def approve_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.role not in [User.Role.STUDENT, User.Role.STAFF]:
        messages.error(request, "Only Student/Staff accounts can be approved here.")
        return redirect("accounts:admin_dashboard")

    if not user.is_active:
        messages.error(request, "This account is deactivated. Reactivate it first.")
        return redirect("accounts:admin_dashboard")

    user.is_approved = True
    user.save(update_fields=["is_approved"])

    # Optional email
    if send_approval_email and user.email:
        try:
            send_approval_email(user)
        except Exception:
            pass

    messages.success(request, f"Approved: {user.username}")
    return redirect("accounts:admin_dashboard")


@admin_required
@require_POST
def reject_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.role not in [User.Role.STUDENT, User.Role.STAFF]:
        messages.error(request, "Only Student/Staff accounts can be rejected here.")
        return redirect("accounts:admin_dashboard")

    user.is_active = False
    user.is_approved = False
    user.save(update_fields=["is_active", "is_approved"])

    messages.warning(request, f"Deactivated: {user.username}")
    return redirect("accounts:admin_dashboard")


@admin_required
@require_POST
def change_role_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get("role")

    allowed = {User.Role.STUDENT, User.Role.STAFF, User.Role.ADMIN}
    if new_role not in allowed:
        messages.error(request, "Invalid role.")
        return redirect("accounts:admin_dashboard")

    user.role = new_role
    user.save(update_fields=["role"])
    messages.success(request, f"Updated role: {user.username} → {new_role}")
    return redirect("accounts:admin_dashboard")


@never_cache
@admin_required
def admin_users_view(request):
    q = (request.GET.get("q") or "").strip()
    role = (request.GET.get("role") or "").strip()
    approved = (request.GET.get("approved") or "").strip()

    users = User.objects.all().order_by("-date_joined")

    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
    if role:
        users = users.filter(role=role)
    if approved == "yes":
        users = users.filter(is_approved=True)
    if approved == "no":
        users = users.filter(is_approved=False)

    return render(request, "accounts/admin_users.html", {
        "users": users,
        "q": q,
        "role": role,
        "approved": approved,
    })


@admin_required
@require_POST
def toggle_active_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    messages.success(request, f"{'Activated' if user.is_active else 'Deactivated'}: {user.username}")
    return redirect("accounts:admin_users")


@admin_required
@require_POST
def resend_approval_email_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if not user.email:
        messages.error(request, "No email found for this user.")
        return redirect("accounts:admin_users")

    if send_approval_email:
        try:
            send_approval_email(user)
            messages.success(request, f"Approval email resent to {user.email}")
        except Exception as e:
            messages.error(request, f"Failed to send email: {e}")
    else:
        messages.warning(request, "Email helper not configured.")

    return redirect("accounts:admin_users")
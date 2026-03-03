from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.models import User
from notices.models import Notice

# optional modules (safe)
try:
    from payments.models import PaymentProof
except Exception:
    PaymentProof = None

try:
    from lostfound.models import ClaimRequest
except Exception:
    ClaimRequest = None

try:
    from events.models import Event
except Exception:
    Event = None


def _staff_or_admin(user):
    return user.is_authenticated and (
        getattr(user, "is_superuser", False)
        or getattr(user, "role", None) in [User.Role.STAFF, User.Role.ADMIN]
    )


@never_cache
@login_required
def staff_dashboard_view(request):
    if not _staff_or_admin(request.user):
        return render(request, "403.html", status=403)

    now = timezone.now()

    # =========================
    # EVENTS (DB dynamic, consistent)
    # =========================
    active_events_qs = []
    active_events_count = 0
    published_events_count = 0
    recent_events = []

    if Event:
        # IMPORTANT: consistent definition (same as admin)
        active_events_qs = Event.objects.filter(is_active=True, archived_at__isnull=True)

        active_events_count = active_events_qs.count()

        # Only published (if you want this as a separate stat)
        published_events_count = active_events_qs.filter(status="published").count()

        # Optional: show latest events list in UI later
        recent_events = active_events_qs.order_by("-created_at")[:5]

    # =========================
    # NOTICES
    # =========================
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    published_count = Notice.objects.filter(is_active=True).count()

    # =========================
    # PAYMENTS (pending)
    # =========================
    payments_pending_count = 0
    pending_proofs = []

    if PaymentProof:
        base = PaymentProof.objects.select_related("registration__event", "registration__user")
        payments_pending_count = base.filter(status="pending").count()

        # Safe ordering (some projects use submitted_at, others created_at)
        if hasattr(PaymentProof, "submitted_at"):
            order_field = "-submitted_at"
        elif hasattr(PaymentProof, "created_at"):
            order_field = "-created_at"
        else:
            order_field = "-id"

        pending_proofs = base.filter(status="pending").order_by(order_field)[:6]

    # =========================
    # LOST & FOUND CLAIMS (pending)
    # =========================
    pending_claims_count = 0
    if ClaimRequest:
        pending_claims_count = ClaimRequest.objects.filter(status="pending").count()

    # =========================
    # CONTEXT (NO CRASH GUARANTEE)
    # =========================
    context = {
        # Notices
        "recent_notices": recent_notices,
        "published_count": published_count,

        # Payments
        "payments_pending_count": payments_pending_count,
        "pending_proofs": pending_proofs,

        # Claims + Events
        "pending_claims_count": pending_claims_count,
        "published_events_count": published_events_count,

        # ✅ aliases expected by your template
        "active_events": active_events_count,
        "pending_claims": pending_claims_count,

        # Optional (for future UI sections)
        "recent_events": recent_events,

        # UI
        "refresh_seconds": 30,
        "year": now.year,

        # navbar safe
        "unread_count": 0,
    }

    return render(request, "staff/dashboard.html", context)
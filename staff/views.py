from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.models import User, UserProfile
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

    # ✅ LOAD PROFILE
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # =========================
    # EVENTS
    # =========================
    active_events_count = 0
    published_events_count = 0
    recent_events = []

    if Event:
        active_events_qs = Event.objects.filter(is_active=True, archived_at__isnull=True)

        active_events_count = active_events_qs.count()
        published_events_count = active_events_qs.filter(status="published").count()
        recent_events = active_events_qs.order_by("-created_at")[:5]

    # =========================
    # NOTICES
    # =========================
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    published_count = Notice.objects.filter(is_active=True).count()

    # =========================
    # PAYMENTS
    # =========================
    payments_pending_count = 0
    pending_proofs = []

    if PaymentProof:
        base = PaymentProof.objects.select_related(
            "registration__event",
            "registration__user"
        )

        payments_pending_count = base.filter(status="pending").count()

        if hasattr(PaymentProof, "submitted_at"):
            order_field = "-submitted_at"
        elif hasattr(PaymentProof, "created_at"):
            order_field = "-created_at"
        else:
            order_field = "-id"

        pending_proofs = base.filter(status="pending").order_by(order_field)[:6]

    # =========================
    # CLAIMS
    # =========================
    pending_claims_count = 0
    pending_claims_qs = []
    if ClaimRequest:
        pending_claims_qs = ClaimRequest.objects.filter(status="pending").select_related("item", "student").order_by("-created_at")[:5]
        pending_claims_count = ClaimRequest.objects.filter(status="pending").count()

    context = {
        # profile
        "profile": profile,

        # notices
        "recent_notices": recent_notices,
        "published_count": published_count,

        # payments
        "payments_pending_count": payments_pending_count,
        "pending_proofs": pending_proofs,

        # events
        "published_events_count": published_events_count,
        "active_events": active_events_count,
        "recent_events": recent_events,

        # claims — pending_claims MUST come after pending_claims_count
        # to avoid Django template variable resolution issues
        "pending_claims_count": pending_claims_count,
        "pending_claims": list(pending_claims_qs),

        # UI
        "refresh_seconds": 30,
        "year": now.year,
        "unread_count": 0,
    }

    return render(request, "staff/dashboard.html", context)
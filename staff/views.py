from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q


from notices.models import Notice
from accounts.models import User

# optional modules
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
    return user.is_authenticated and (user.is_superuser or getattr(user, "role", None) in [User.Role.STAFF, User.Role.ADMIN])


@login_required
def staff_dashboard_view(request):
    if not _staff_or_admin(request.user):
        # you can redirect to landing if you want
        return render(request, "403.html", status=403)

    # Notices
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    published_count = Notice.objects.filter(is_active=True).count()

    # Pending payments widget
    payments_pending_count = 0
    pending_proofs = []
    if PaymentProof:
        base = PaymentProof.objects.select_related("registration__event", "registration__user")
        payments_pending_count = base.filter(status="pending").count()
        pending_proofs = base.filter(status="pending").order_by("-submitted_at")[:6]

    # Optional: Pending claims count (lostfound)
    pending_claims_count = 0
    if ClaimRequest:
        pending_claims_count = ClaimRequest.objects.filter(status="pending").count()

    # Optional: Published events count
    published_events_count = 0
    if Event:
        published_events_count = Event.objects.filter(status="published").count()

    return render(request, "staff/dashboard.html", {
        "recent_notices": recent_notices,
        "published_count": published_count,

        "payments_pending_count": payments_pending_count,
        "pending_proofs": pending_proofs,

        "pending_claims_count": pending_claims_count,
        "published_events_count": published_events_count,

        # auto refresh
        "refresh_seconds": 30,
        "year": timezone.now().year,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from notices.models import Notice

# Optional: Lost & Found
try:
    from lostfound.models import ClaimRequest
except Exception:
    ClaimRequest = None

# Optional: Payments
try:
    from payments.models import PaymentProof
except Exception:
    PaymentProof = None


@login_required
def staff_dashboard_view(request):
    # Notices
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    published_count = Notice.objects.filter(is_active=True).count()

    # Payments summary
    payments_pending_count = 0
    pending_proofs = []

    if PaymentProof:
        base = PaymentProof.objects.select_related("registration__event", "registration__user")
        payments_pending_count = base.filter(status="pending").count()
        pending_proofs = base.filter(status="pending").order_by("-submitted_at")[:5]

    # Lost & Found pending claims summary
    pending_claims_count = 0
    pending_claims = []

    if ClaimRequest:
        qs = ClaimRequest.objects.select_related("item", "student").filter(status="pending")
        pending_claims_count = qs.count()
        pending_claims = qs.order_by("-created_at")[:5]

    return render(request, "staff/dashboard.html", {
        "recent_notices": recent_notices,
        "published_count": published_count,

        "payments_pending_count": payments_pending_count,
        "pending_proofs": pending_proofs,

        "pending_claims_count": pending_claims_count,
        "pending_claims": pending_claims,
    })

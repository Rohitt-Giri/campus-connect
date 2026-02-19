from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from notices.models import Notice
from notices.permissions import can_manage_notices

try:
    from lostfound.models import ClaimRequest
except Exception:
    ClaimRequest = None


@login_required
def staff_dashboard_view(request):
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    published_count = Notice.objects.filter(is_active=True).count()

    pending_claims = 0
    if ClaimRequest:
        pending_claims = ClaimRequest.objects.filter(status="pending").count()

    return render(request, "staff/dashboard.html", {
        "recent_notices": recent_notices,
        "published_count": published_count,
        "can_manage": can_manage_notices(request.user),
        "pending_claims": pending_claims,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from notices.models import Notice
from notices.permissions import can_manage_notices

@login_required
def staff_dashboard_view(request):
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    published_count = Notice.objects.filter(is_active=True).count()

    return render(request, "staff/dashboard.html", {
        "recent_notices": recent_notices,
        "published_count": published_count,
        "can_manage": can_manage_notices(request.user),
    })

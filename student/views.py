from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from notices.models import Notice

@login_required
def student_dashboard_view(request):
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    notices_count = Notice.objects.filter(is_active=True).count()

    return render(request, "student/dashboard.html", {
        "recent_notices": recent_notices,
        "notices_count": notices_count,
    })

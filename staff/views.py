from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count

from accounts.models import User
from events.models import Event

# If your notices app name/model differs, adjust this import
from notices.models import Notice


@login_required
def staff_dashboard_view(request):
    # Only staff/admin allowed
    if request.user.role not in [User.Role.STAFF, User.Role.ADMIN]:
        return redirect("student:dashboard")

    now = timezone.now()

    # EVENTS
    active_events = Event.objects.filter(status="published", start_datetime__gte=now).count()
    recent_events = (
        Event.objects.all()
        .order_by("-created_at")[:5]
    )

    top_events = (
        Event.objects.annotate(reg_count=Count("registrations"))
        .order_by("-reg_count", "start_datetime")[:5]
    )

    # NOTICES
    published_count = Notice.objects.count()
    recent_notices = Notice.objects.order_by("-created_at")[:5]

    context = {
        "active_events": active_events,
        "recent_events": recent_events,
        "top_events": top_events,
        "published_count": published_count,
        "recent_notices": recent_notices,
    }
    return render(request, "staff/dashboard.html", context)

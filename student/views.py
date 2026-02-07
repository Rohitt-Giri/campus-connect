from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import User
from events.models import Event, EventRegistration
from notices.models import Notice  # adjust if needed


@login_required
def student_dashboard_view(request):
    now = timezone.now()

    # ✅ Notices (your model uses is_active, NOT status)
    recent_notices = (
        Notice.objects.filter(is_active=True)
        .order_by("-created_at")[:5]
    )
    notices_count = Notice.objects.filter(is_active=True).count()

    # ✅ Events
    upcoming_events = (
        Event.objects.filter(status="published", start_datetime__gte=now)
        .order_by("start_datetime")[:5]
    )
    upcoming_events_count = Event.objects.filter(
        status="published", start_datetime__gte=now
    ).count()

    # ✅ Student registrations
    my_regs = (
        EventRegistration.objects.filter(user=request.user)
        .select_related("event")
        .order_by("-registered_at")[:5]
    )
    my_registrations_count = EventRegistration.objects.filter(user=request.user).count()

    context = {
        "recent_notices": recent_notices,
        "notices_count": notices_count,

        "upcoming_events": upcoming_events,
        "upcoming_events_count": upcoming_events_count,

        "my_regs": my_regs,
        "my_registrations_count": my_registrations_count,

        # you can keep these for future modules
        "payments_pending_count": 0,
    }
    return render(request, "student/dashboard.html", context)
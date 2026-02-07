from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.models import User
from events.models import Event, EventRegistration
from notices.models import Notice


@login_required
def student_dashboard_view(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("staff:dashboard")

    now = timezone.now()

    upcoming_events = Event.objects.filter(status="published", start_datetime__gte=now).order_by("start_datetime")[:6]
    upcoming_events_count = Event.objects.filter(status="published", start_datetime__gte=now).count()

    my_regs = (
        EventRegistration.objects.filter(user=request.user)
        .select_related("event")
        .order_by("-registered_at")[:6]
    )
    my_registrations_count = EventRegistration.objects.filter(user=request.user).count()

    recent_notices = Notice.objects.order_by("-created_at")[:6]
    notices_count = Notice.objects.count()

    context = {
        "upcoming_events": upcoming_events,
        "upcoming_events_count": upcoming_events_count,
        "my_regs": my_regs,
        "my_registrations_count": my_registrations_count,
        "recent_notices": recent_notices,
        "notices_count": notices_count,
    }
    return render(request, "student/dashboard.html", context)

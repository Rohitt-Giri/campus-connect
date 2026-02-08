from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.apps import apps

from accounts.models import User
from events.models import Event, EventRegistration
from notices.models import Notice


def safe_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


@login_required
def student_dashboard_view(request):
    if request.user.role != User.Role.STUDENT:
        return render(request, "student/dashboard.html", {"error": "Not a student account."})

    now = timezone.now()

    upcoming_events = Event.objects.filter(status="published", start_datetime__gte=now).order_by("start_datetime")[:5]
    upcoming_events_count = Event.objects.filter(status="published", start_datetime__gte=now).count()

    my_regs = EventRegistration.objects.filter(user=request.user).select_related("event").order_by("-registered_at")[:5]
    my_registrations_count = EventRegistration.objects.filter(user=request.user).count()

    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:5]
    notices_count = Notice.objects.filter(is_active=True).count()

    # Payments (safe)
    PaymentProof = safe_model("payments", "PaymentProof")
    payments_pending_count = 0
    if PaymentProof:
        payments_pending_count = PaymentProof.objects.filter(
            registration__user=request.user,
            status="pending"
        ).count()

    context = {
        "upcoming_events": upcoming_events,
        "upcoming_events_count": upcoming_events_count,
        "my_regs": my_regs,
        "my_registrations_count": my_registrations_count,
        "recent_notices": recent_notices,
        "notices_count": notices_count,
        "payments_pending_count": payments_pending_count,
    }
    return render(request, "student/dashboard.html", context)

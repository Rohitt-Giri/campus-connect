from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count
from django.apps import apps

from accounts.models import User
from events.models import Event
from notices.models import Notice


def safe_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


@login_required
def staff_dashboard_view(request):
    if request.user.role not in [User.Role.STAFF, User.Role.ADMIN]:
        return render(request, "staff/dashboard.html", {"error": "Not a staff/admin account."})

    now = timezone.now()

    active_events = Event.objects.filter(status="published", start_datetime__gte=now).count()
    recent_events = Event.objects.order_by("-created_at")[:5]

    top_events = (
        Event.objects.annotate(reg_count=Count("registrations"))
        .order_by("-reg_count", "-start_datetime")[:5]
    )

    published_count = Notice.objects.filter(is_active=True).count()
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:5]

    # Lost&Found safe
    ClaimRequest = safe_model("lostfound", "ClaimRequest")
    pending_claims = 0
    if ClaimRequest:
        pending_claims = ClaimRequest.objects.filter(status="pending").count()

    # Payments safe
    PaymentProof = safe_model("payments", "PaymentProof")
    pending_payments_count = 0
    if PaymentProof:
        pending_payments_count = PaymentProof.objects.filter(status="pending").count()

    context = {
        "active_events": active_events,
        "recent_events": recent_events,
        "top_events": top_events,
        "published_count": published_count,
        "recent_notices": recent_notices,
        "pending_claims": pending_claims,
        "pending_payments_count": pending_payments_count,
    }
    return render(request, "staff/dashboard.html", context)

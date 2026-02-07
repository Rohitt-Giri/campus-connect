from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import User
from events.models import Event
from notices.models import Notice  # adjust if your Notice model name differs


def _is_staff_like(user) -> bool:
    return getattr(user, "role", None) in (User.Role.STAFF, User.Role.ADMIN) or user.is_staff or user.is_superuser


@login_required
def staff_dashboard_view(request):
    if not _is_staff_like(request.user):
        return redirect("core:landing")

    now = timezone.now()

    active_events = Event.objects.filter(status="published", start_datetime__gte=now).count()
    recent_events = Event.objects.all().order_by("-created_at")[:5]

    top_events = (
        Event.objects.annotate(reg_count=Count("registrations"))
        .order_by("-reg_count", "-start_datetime")[:5]
    )

    published_count = Notice.objects.filter(is_active=True).count()

    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:5]

    context = {
        "active_events": active_events,
        "recent_events": recent_events,
        "top_events": top_events,
        "published_count": published_count,
        "recent_notices": recent_notices,
        "pending_claims": 0,  # placeholder for future Lost&Found module
        "year": now.year,
    }
    return render(request, "staff/dashboard.html", context)

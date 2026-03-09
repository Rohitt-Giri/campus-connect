from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from notices.models import Notice
from accounts.models import UserProfile

# optional modules
try:
    from lostfound.models import LostFoundItem, ClaimRequest
except Exception:
    LostFoundItem = None
    ClaimRequest = None

try:
    from events.models import Event, EventRegistration
except Exception:
    Event = None
    EventRegistration = None

try:
    from payments.models import PaymentProof
except Exception:
    PaymentProof = None


@never_cache
@login_required
def student_dashboard_view(request):
    now = timezone.now()

    # profile (for dashboard avatar/photo)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # notices
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    notices_count = Notice.objects.filter(is_active=True).count()

    # lost & found
    my_posts_count = 0
    my_claims_count = 0
    my_items_count = 0

    if LostFoundItem:
        my_posts_count = LostFoundItem.objects.filter(created_by_id=request.user.id).count()
        my_items_count = my_posts_count

    if ClaimRequest:
        my_claims_count = ClaimRequest.objects.filter(student_id=request.user.id).count()

    # events
    next_event = None
    upcoming_events_count = 0
    events_joined_count = 0

    if Event:
        try:
            next_event = Event.objects.filter(
                is_active=True,
                archived_at__isnull=True,
                status="published",
                start_datetime__gte=now,
            ).order_by("start_datetime").first()

            upcoming_events_count = Event.objects.filter(
                is_active=True,
                archived_at__isnull=True,
                status="published",
                start_datetime__gte=now,
            ).count()
        except Exception:
            next_event = Event.objects.filter(
                status="published",
                start_datetime__gte=now,
            ).order_by("start_datetime").first()

            upcoming_events_count = Event.objects.filter(
                status="published",
                start_datetime__gte=now,
            ).count()

    if EventRegistration:
        events_joined_count = EventRegistration.objects.filter(user=request.user).count()

    # payments
    payments_pending_count = 0
    if PaymentProof:
        payments_pending_count = PaymentProof.objects.filter(
            registration__user=request.user,
            status="pending"
        ).count()

    # simple recent activity
    recent_activity = []

    if EventRegistration:
        latest_regs = EventRegistration.objects.filter(
            user=request.user
        ).select_related("event").order_by("-registered_at")[:2]

        for r in latest_regs:
            recent_activity.append({
                "title": f"Registered for {r.event.title}",
                "time": r.registered_at.strftime("%b %d, %Y"),
                "tag": "Event",
            })

    if PaymentProof:
        latest_payments = PaymentProof.objects.filter(
            registration__user=request.user
        ).select_related("registration__event").order_by("-id")[:2]

        for p in latest_payments:
            recent_activity.append({
                "title": f"Payment submitted for {p.registration.event.title}",
                "time": getattr(p, "created_at", None).strftime("%b %d, %Y") if getattr(p, "created_at", None) else "Recently",
                "tag": "Payment",
            })

    recent_activity = recent_activity[:4]

    return render(request, "student/dashboard.html", {
        "now": now,
        "profile": profile,

        "recent_notices": recent_notices,
        "notices_count": notices_count,

        "my_posts_count": my_posts_count,
        "my_claims_count": my_claims_count,
        "my_items_count": my_items_count,

        "next_event": next_event,
        "upcoming_events_count": upcoming_events_count,
        "events_joined_count": events_joined_count,

        "payments_pending_count": payments_pending_count,
        "recent_activity": recent_activity,

        "unread_count": 0,
    })
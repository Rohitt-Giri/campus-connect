from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts.models import UserProfile
from notices.models import Notice

# Events / registrations
try:
    from events.models import Event, EventRegistration
except Exception:
    Event = None
    EventRegistration = None

# Lost & found
try:
    from lostfound.models import LostFoundItem, ClaimRequest
except Exception:
    LostFoundItem = None
    ClaimRequest = None

# Payments
try:
    from payments.models import PaymentProof
except Exception:
    PaymentProof = None

# Notifications
try:
    from notifications.models import Notification
except Exception:
    Notification = None


@never_cache
@login_required
def student_dashboard_view(request):
    now = timezone.now()

    # Profile
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Notices
    recent_notices = Notice.objects.filter(is_active=True).order_by("-created_at")[:3]
    notices_count = Notice.objects.filter(is_active=True).count()

    # Lost & Found
    my_posts_count = 0
    my_claims_count = 0
    my_items_count = 0

    if LostFoundItem:
        my_posts_count = LostFoundItem.objects.filter(created_by=request.user).count()
        my_items_count = my_posts_count

    if ClaimRequest:
        my_claims_count = ClaimRequest.objects.filter(student=request.user).count()

    # Events
    next_event = None
    upcoming_events_count = 0
    events_joined_count = 0

    if Event:
        try:
            base_events = Event.objects.filter(
                is_active=True,
                archived_at__isnull=True,
                status="published",
            )
        except Exception:
            base_events = Event.objects.filter(status="published")

        next_event = base_events.filter(
            start_datetime__gte=now
        ).order_by("start_datetime").first()

        upcoming_events_count = base_events.filter(
            start_datetime__gte=now
        ).count()

    if EventRegistration:
        events_joined_count = EventRegistration.objects.filter(user=request.user).count()

    # Payments
    payments_pending_count = 0
    if PaymentProof:
        payments_pending_count = PaymentProof.objects.filter(
            registration__user=request.user,
            status="pending"
        ).count()

    # Notifications
    unread_count = 0
    if Notification:
        try:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        except Exception:
            unread_count = 0

    # Recent activity
    activity_feed = []

    if EventRegistration:
        latest_regs = (
            EventRegistration.objects
            .filter(user=request.user)
            .select_related("event")
            .order_by("-registered_at")[:3]
        )

        for reg in latest_regs:
            activity_feed.append({
                "title": f"Registered for {reg.event.title}",
                "time": reg.registered_at,
                "tag": "Event",
            })

    if PaymentProof:
        latest_payments = (
            PaymentProof.objects
            .filter(registration__user=request.user)
            .select_related("registration__event")
            .order_by("-id")[:3]
        )

        for proof in latest_payments:
            proof_time = getattr(proof, "created_at", None) or now
            activity_feed.append({
                "title": f"Payment submitted for {proof.registration.event.title}",
                "time": proof_time,
                "tag": "Payment",
            })

    for notice in recent_notices:
        activity_feed.append({
            "title": f"New notice: {notice.title}",
            "time": notice.created_at,
            "tag": "Notice",
        })

    # Sort newest first
    activity_feed.sort(key=lambda x: x["time"], reverse=True)

    recent_activity = []
    for item in activity_feed[:4]:
        recent_activity.append({
            "title": item["title"],
            "time": item["time"].strftime("%b %d, %Y"),
            "tag": item["tag"],
        })

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

        "unread_count": unread_count,
    })


@login_required
def my_registrations_view(request):
    registrations = (
        EventRegistration.objects
        .select_related("event")
        .filter(user=request.user)
        .order_by("-registered_at")
    )

    q = (request.GET.get("q") or "").strip()
    reg_type = (request.GET.get("type") or "all").strip()
    time_filter = (request.GET.get("time") or "all").strip()

    if q:
        registrations = registrations.filter(
            Q(event__title__icontains=q) |
            Q(event__location__icontains=q)
        )

    if reg_type == "free":
        registrations = registrations.filter(event__is_paid=False)
    elif reg_type == "paid":
        registrations = registrations.filter(event__is_paid=True)

    now = timezone.now()

    if time_filter == "upcoming":
        registrations = registrations.filter(event__start_datetime__gte=now)
    elif time_filter == "past":
        registrations = registrations.filter(event__start_datetime__lt=now)

    paginator = Paginator(registrations, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "student/my_registrations.html",
        {
            "registrations": page_obj,
            "page_obj": page_obj,
            "q": q,
            "reg_type": reg_type,
            "time_filter": time_filter,
            "now": now,
        },
    )
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import RegisterForm, ProfileForm
from .models import User, UserProfile

# =========================
# OPTIONAL MODULE IMPORTS
# =========================
try:
    from events.models import Event, EventRegistration
except Exception:
    Event = None
    EventRegistration = None

try:
    from payments.models import PaymentProof
except Exception:
    PaymentProof = None

try:
    from lostfound.models import ClaimRequest, LostFoundItem
except Exception:
    ClaimRequest = None
    LostFoundItem = None

try:
    from notices.models import Notice
except Exception:
    Notice = None

try:
    from audit.models import AuditLog
except Exception:
    AuditLog = None


# ==========================================================
# AUTH / BASIC PAGES
# ==========================================================
@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:post_login_redirect")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created. Please wait for admin approval.")
            return redirect("accounts:pending")
        messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@never_cache
def pending_approval_view(request):
    return render(request, "accounts/pending_approval.html")


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:post_login_redirect")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password.")
            return redirect("accounts:login")

        if not user.is_active:
            messages.error(request, "Your account was deactivated. Please contact admin.")
            return redirect("accounts:login")

        if user.role in [User.Role.STUDENT, User.Role.STAFF] and not user.is_approved:
            return redirect("accounts:pending")

        login(request, user)
        return redirect("accounts:post_login_redirect")

    return render(request, "accounts/login.html")


@login_required
def post_login_redirect_view(request):
    user = request.user

    if user.is_superuser or user.role == User.Role.ADMIN:
        return redirect("accounts:admin_dashboard")

    if user.role == User.Role.STUDENT:
        return redirect("student:dashboard")

    if user.role == User.Role.STAFF:
        return redirect("staff:dashboard")

    messages.error(request, "User role not recognized.")
    return redirect("accounts:login")


@never_cache
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


# ==========================================================
# PROFILE
# ==========================================================
@login_required
def my_profile_view(request):
    profile, _created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"created_at": timezone.now(), "updated_at": timezone.now()},
    )

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated ✅")
            return redirect("accounts:my_profile")
        messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, "accounts/my_profile.html", {"form": form, "profile": profile})


# ==========================================================
# ADMIN DASHBOARD (FULL DB DYNAMIC + CONSISTENT COUNTS)
# ==========================================================
@never_cache
@admin_required
def admin_dashboard_view(request):
    now = timezone.now()

    pending_users = User.objects.filter(
        role__in=[User.Role.STUDENT, User.Role.STAFF],
        is_approved=False,
        is_active=True
    ).order_by("-date_joined")

    students_total = User.objects.filter(role=User.Role.STUDENT, is_active=True).count()
    staff_total = User.objects.filter(role=User.Role.STAFF, is_active=True).count()
    pending_total = pending_users.count()

    # =========================
    # EVENTS (FORCE CONSISTENCY)
    # =========================
    events_all_active_total = 0
    events_published_total = 0
    upcoming_events_count = 0
    latest_events = []

    if Event:
        base_active = Event.objects.filter(is_active=True, archived_at__isnull=True)
        events_all_active_total = base_active.count()

        published_active = base_active.filter(status="published")
        events_published_total = published_active.count()

        upcoming_events_count = published_active.filter(start_datetime__gte=now).count()
        latest_events = published_active.order_by("-created_at")[:5]

    # Registrations
    registrations_total = EventRegistration.objects.count() if EventRegistration else 0

    # Notices
    notices_total = Notice.objects.filter(is_active=True).count() if Notice else 0

    # Payments
    pending_payments = approved_payments = rejected_payments = 0
    payments_pending = []
    if PaymentProof:
        pay_qs = PaymentProof.objects.select_related("registration__event", "registration__user")
        pending_payments = pay_qs.filter(status="pending").count()
        approved_payments = pay_qs.filter(status="approved").count()
        rejected_payments = pay_qs.filter(status="rejected").count()
        order_field = "-submitted_at" if hasattr(PaymentProof, "submitted_at") else "-id"
        payments_pending = pay_qs.filter(status="pending").order_by(order_field)[:5]

    # Lost & Found
    items_total = LostFoundItem.objects.count() if LostFoundItem else 0
    pending_claims = 0
    pending_claims_list = []
    if ClaimRequest:
        pending_claims = ClaimRequest.objects.filter(status="pending").count()
        order_field = "-created_at" if hasattr(ClaimRequest, "created_at") else "-id"
        pending_claims_list = ClaimRequest.objects.select_related("student", "item").filter(
            status="pending"
        ).order_by(order_field)[:5]

    # Logs
    recent_logs = AuditLog.objects.select_related("actor").order_by("-created_at")[:10] if AuditLog else []

    # ✅ MAIN STATS
    stats = {
        "students_total": students_total,
        "staff_total": staff_total,
        "pending_total": pending_total,

        # ✅ force events_total to ALWAYS be PUBLISHED total
        "events_total": events_published_total,
        "events_published_total": events_published_total,
        "events_all_active_total": events_all_active_total,

        "registrations_total": registrations_total,
        "notices_total": notices_total,
        "pending_payments": pending_payments,
        "pending_claims": pending_claims,
    }

    overview = {
        "upcoming_events_count": upcoming_events_count,
        "latest_events": latest_events,
        "payments_counts": {
            "pending": pending_payments,
            "approved": approved_payments,
            "rejected": rejected_payments,
        },
        "payments_pending": payments_pending,
        "lostfound_counts": {
            "items": items_total,
            "pending_claims": pending_claims,
        },
        "pending_claims": pending_claims_list,
    }

    # ✅ ADD TOP-LEVEL ALIASES TOO (so template can't mess it up)
    context = {
        "pending_users": pending_users,
        "stats": stats,
        "overview": overview,
        "recent_logs": recent_logs,

        # aliases (if template uses these)
        "events_total": events_published_total,
        "published_events_count": events_published_total,

        "unread_count": 0,
        "year": now.year,
    }

    # ✅ DEBUG: print to console so we know EXACTLY what server is using
    print("ADMIN DASHBOARD COUNTS:",
          "published=", events_published_total,
          "all_active=", events_all_active_total)

    return render(request, "accounts/admin_dashboard.html", context)


# ==========================================================
# ADMIN ACTIONS
# ==========================================================
@admin_required
@require_POST
def approve_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.role not in [User.Role.STUDENT, User.Role.STAFF]:
        messages.error(request, "Only Student/Staff accounts can be approved here.")
        return redirect("accounts:admin_dashboard")

    if not user.is_active:
        messages.error(request, "This account is deactivated. Reactivate it first if needed.")
        return redirect("accounts:admin_dashboard")

    user.is_approved = True
    user.save(update_fields=["is_approved"])

    messages.success(request, f"Approved: {user.username}")
    return redirect("accounts:admin_dashboard")


@admin_required
@require_POST
def reject_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.role not in [User.Role.STUDENT, User.Role.STAFF]:
        messages.error(request, "Only Student/Staff accounts can be rejected here.")
        return redirect("accounts:admin_dashboard")

    user.is_active = False
    user.is_approved = False
    user.save(update_fields=["is_active", "is_approved"])

    messages.warning(request, f"Deactivated: {user.username}")
    return redirect("accounts:admin_dashboard")
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_POST

from audit.utils import log_action
from accounts.models import User
from payments.models import PaymentProof
from notifications.utils import notify

from events.email_utils import send_event_registration_email
from .models import Event, EventRegistration
from .forms import EventForm, EventRegistrationForm


def _staff_or_admin(user):
    if not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    return getattr(user, "role", None) in [User.Role.STAFF, User.Role.ADMIN]


@login_required
def events_list_view(request):
    # Students see only published + active
    events = Event.objects.filter(status="published", is_active=True).order_by("start_datetime")
    return render(request, "events/events_list.html", {"events": events})


@login_required
def event_create_view(request):
    # ✅ Staff/Admin only
    if not _staff_or_admin(request.user):
        messages.error(request, "Only staff/admin can create events.")
        return redirect("events:list")

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user

            will_publish = (event.status == "published")
            now = timezone.now()

            # set published timestamp if publishing now
            if will_publish and not getattr(event, "published_at", None):
                event.published_at = now

            # ensure active default
            if getattr(event, "is_active", None) is None:
                event.is_active = True

            event.save()

            # ✅ In-app notification (students) only once
            if will_publish and not getattr(event, "notified_at", None):
                students = User.objects.filter(
                    role=User.Role.STUDENT,
                    is_active=True,
                    is_approved=True
                ).only("id")

                for student in students:
                    notify(
                        student,
                        title="New event published ✅",
                        message=f"{event.title} is now available. Tap to view & register.",
                        url=reverse("events:detail", kwargs={"pk": event.id}),
                        category="event",
                    )

                event.notified_at = now
                event.save(update_fields=["notified_at"])

            messages.success(request, "Event created successfully ✅")
            return redirect("events:detail", pk=event.pk)

        messages.error(request, "Please fix the errors below.")
    else:
        form = EventForm()

    return render(request, "events/event_form.html", {"form": form, "is_edit": False})


@login_required
def event_edit_view(request, pk):
    # ✅ Staff/Admin only
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            updated = form.save(commit=False)

            # if draft -> published, set published_at
            if updated.status == "published" and not updated.published_at:
                updated.published_at = timezone.now()

            updated.save()

            messages.success(request, "Event updated ✅")
            return redirect("events:detail", pk=event.pk)

        messages.error(request, "Please fix the errors below.")
    else:
        form = EventForm(instance=event)

    return render(request, "events/event_form.html", {"form": form, "event": event, "is_edit": True})


@login_required
def event_archive_confirm_view(request, pk):
    # ✅ Staff/Admin only
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)
    return render(request, "events/event_archive_confirm.html", {"event": event})


@login_required
@require_POST
def event_archive_view(request, pk):
    # ✅ Staff/Admin only
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)

    event.is_active = False
    # optional but nice: once archived, it shouldn't remain "published"
    if event.status == "published":
        event.status = "draft"

    # this field is optional - only if you added it in DB
    if hasattr(event, "archived_at"):
        event.archived_at = timezone.now()

    # save safely depending on your model fields
    update_fields = ["is_active", "status"]
    if hasattr(event, "archived_at"):
        update_fields.append("archived_at")

    event.save(update_fields=update_fields)

    messages.success(request, "Event archived ✅")
    return redirect("events:list")


@login_required
def event_detail_view(request, pk):
    # Staff/Admin can open any event (draft/archived too)
    if _staff_or_admin(request.user):
        event = get_object_or_404(Event, pk=pk)
    else:
        # Students: only published + active
        event = get_object_or_404(Event, pk=pk, status="published", is_active=True)

    registration = EventRegistration.objects.filter(event=event, user=request.user).first()
    is_registered = registration is not None

    payment_proof = None
    if is_registered and event.is_paid:
        payment_proof = getattr(registration, "payment_proof", None)

    return render(request, "events/event_detail.html", {
        "event": event,
        "registration": registration,
        "is_registered": is_registered,
        "payment_proof": payment_proof,
        "PAYMENT_QR_URL": getattr(settings, "PAYMENT_QR_URL", ""),
        "now": timezone.now(),
    })


@login_required
def event_register_view(request, pk):
    # Students can only register published + active
    event = get_object_or_404(Event, pk=pk, status="published", is_active=True)

    # ✅ Only students can register (admin superuser allowed)
    if not (request.user.is_superuser or request.user.role == User.Role.STUDENT):
        messages.error(request, "Only students can register for events.")
        return redirect("events:detail", pk=event.id)

    # ✅ Prevent duplicate registration
    if EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.info(request, "You are already registered for this event.")
        return redirect("events:detail", pk=event.id)

    if request.method == "POST":
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.event = event
            reg.user = request.user
            reg.save()

            # ✅ Send email (FREE vs PAID)
            email_sent = send_event_registration_email(reg)

            # ✅ Audit log
            log_action(
                request=request,
                actor=request.user,
                action="EVENT_REGISTER",
                message=f"Registered for event: {event.title}"
                        + (" (email sent)" if email_sent else " (no email)"),
                target=reg,
                metadata={
                    "event_id": event.id,
                    "is_paid": bool(getattr(event, "is_paid", False)),
                    "price": str(getattr(event, "price", 0)),
                    "email_sent": email_sent,
                    "email": getattr(request.user, "email", "") or "",
                }
            )

            if email_sent:
                messages.success(request, "Registration successful ✅ (Email sent)")
            else:
                messages.success(request, "Registration successful ✅ (No email on your account)")

            return redirect("events:detail", pk=event.id)

        messages.error(request, "Please fix the errors below.")
    else:
        form = EventRegistrationForm(initial={"email": getattr(request.user, "email", "") or ""})

    return render(request, "events/event_register.html", {"event": event, "form": form})


@login_required
def event_registrations_view(request, pk):
    # ✅ Staff/Admin only
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)

    registrations = (
        EventRegistration.objects
        .select_related("user", "event")
        .filter(event=event)
        .order_by("-registered_at")
    )

    proof_map = {}
    if event.is_paid:
        proofs = (
            PaymentProof.objects
            .select_related("verified_by", "registration", "registration__user", "registration__event")
            .filter(registration__in=registrations)
        )
        proof_map = {p.registration_id: p for p in proofs}

    return render(request, "events/event_registrations.html", {
        "event": event,
        "registrations": registrations,
        "proof_map": proof_map,
    })
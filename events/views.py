from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from payments.models import PaymentProof
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
    events = Event.objects.filter(status="published").order_by("start_datetime")
    return render(request, "events/events_list.html", {"events": events})


@login_required
def event_create_view(request):
    # ✅ Staff/Admin only
    if not _staff_or_admin(request.user):
        messages.error(request, "Only staff/admin can create events.")
        return redirect("events:list")

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, "Event created successfully ✅")
            return redirect("events:detail", pk=event.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = EventForm()

    return render(request, "events/event_form.html", {"form": form})


@login_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)

    registration = EventRegistration.objects.filter(
        event=event,
        user=request.user
    ).first()

    is_registered = registration is not None

    payment_proof = None
    if is_registered and event.is_paid:
        payment_proof = getattr(registration, "payment_proof", None)

    return render(request, "events/event_detail.html", {
        "event": event,
        "registration": registration,
        "is_registered": is_registered,
        "payment_proof": payment_proof,
        # If you no longer use this, you can remove it from template too
        "PAYMENT_QR_URL": getattr(settings, "PAYMENT_QR_URL", ""),
    })


@login_required
def event_register_view(request, pk):
    event = get_object_or_404(Event, pk=pk, status="published")

    # ✅ Only students can register
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
            messages.success(request, "Registration successful ✅")
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

    # Proof map: registration_id -> proof
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

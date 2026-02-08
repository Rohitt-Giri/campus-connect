from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from .forms import EventForm, EventRegistrationForm
from .models import Event, EventRegistration


@login_required
def events_list_view(request):
    qs = Event.objects.filter(status="published").order_by("start_datetime")
    return render(request, "events/events_list.html", {"events": qs})


@login_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk, status="published")

    registration = EventRegistration.objects.filter(event=event, user=request.user).first()
    already_registered = registration is not None
    proof = getattr(registration, "payment_proof", None) if registration else None

    reg_count = event.registrations.count()

    return render(request, "events/event_detail.html", {
        "event": event,
        "already_registered": already_registered,
        "registration": registration,
        "proof": proof,
        "reg_count": reg_count,
    })


@login_required
def event_register_view(request, pk):
    if request.user.role != User.Role.STUDENT:
        messages.error(request, "Only students can register for events.")
        return redirect("events:detail", pk=pk)

    event = get_object_or_404(Event, pk=pk, status="published")

    if event.start_datetime <= timezone.now():
        messages.error(request, "Registration closed. This event already started.")
        return redirect("events:detail", pk=pk)

    existing = EventRegistration.objects.filter(event=event, user=request.user).first()
    if existing:
        messages.info(request, "You are already registered for this event.")
        return redirect("events:detail", pk=pk)

    if request.method == "POST":
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.event = event
            reg.user = request.user
            reg.save()
            messages.success(request, "Registered successfully! 🎉")
            return redirect("events:detail", pk=pk)
    else:
        form = EventRegistrationForm(initial={"email": request.user.email or ""})

    return render(request, "events/event_register.html", {"event": event, "form": form})


@login_required
def event_create_view(request):
    if request.user.role not in [User.Role.STAFF, User.Role.ADMIN]:
        messages.error(request, "Only staff/admin can create events.")
        return redirect("events:list")

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Event saved ✅")
            return redirect("events:detail", pk=obj.pk)
    else:
        form = EventForm()

    return render(request, "events/event_form.html", {"form": form})


@login_required
def event_registrations_view(request, pk):
    if request.user.role not in [User.Role.STAFF, User.Role.ADMIN]:
        messages.error(request, "Access denied.")
        return redirect("events:list")

    event = get_object_or_404(Event, pk=pk)
    regs = EventRegistration.objects.filter(event=event).select_related("user").order_by("-registered_at")
    return render(request, "events/event_registrations.html", {"event": event, "regs": regs})

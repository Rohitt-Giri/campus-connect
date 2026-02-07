from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from .forms import EventForm, EventRegistrationForm
from .models import Event, EventRegistration


def _is_staff_like(user) -> bool:
    return getattr(user, "role", None) in (User.Role.STAFF, User.Role.ADMIN) or user.is_staff or user.is_superuser


@login_required
def events_list_view(request):
    # Students: only published upcoming
    qs = Event.objects.filter(status="published").order_by("start_datetime")
    return render(request, "events/events_list.html", {"events": qs})


@login_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk, status="published")

    already_registered = EventRegistration.objects.filter(event=event, user=request.user).exists()
    reg_count = event.registrations.count()

    return render(
        request,
        "events/event_detail.html",
        {"event": event, "already_registered": already_registered, "reg_count": reg_count},
    )


@login_required
def event_register_view(request, pk):
    # Only students can register
    if request.user.role != User.Role.STUDENT:
        messages.error(request, "Only students can register for events.")
        return redirect("events:detail", pk=pk)

    event = get_object_or_404(Event, pk=pk, status="published")

    # Avoid duplicate
    if EventRegistration.objects.filter(event=event, user=request.user).exists():
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
        messages.error(request, "Please fix the errors below.")
    else:
        # Prefill email if available
        initial = {"email": getattr(request.user, "email", "") or ""}
        form = EventRegistrationForm(initial=initial)

    return render(request, "events/event_register_form.html", {"event": event, "form": form})


@login_required
def event_create_view(request):
    # Staff/Admin only
    if not _is_staff_like(request.user):
        messages.error(request, "You are not allowed to create events.")
        return redirect("core:landing")

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Event saved ✅")
            return redirect("events:detail", pk=obj.pk)
        messages.error(request, "Please fix the errors below.")
    else:
        form = EventForm()

    return render(request, "events/event_form.html", {"form": form})


@login_required
def event_registrations_view(request, pk):
    # Staff/Admin only
    if not _is_staff_like(request.user):
        messages.error(request, "You are not allowed to view registrations.")
        return redirect("core:landing")

    event = get_object_or_404(Event, pk=pk)
    regs = (
        EventRegistration.objects.filter(event=event)
        .select_related("user")
        .order_by("-registered_at")
    )
    return render(request, "events/event_registrations.html", {"event": event, "regs": regs})

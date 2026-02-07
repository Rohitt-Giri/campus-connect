from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EventForm, EventRegistrationForm
from .models import Event, EventRegistration


def _is_staff_like(user):
    if user.is_superuser or user.is_staff:
        return True
    # If you have custom role field
    role = getattr(user, "role", None)
    if role in ("STAFF", "ADMIN"):
        return True
    return False


@login_required
def events_list_view(request):
    # Students see only published
    qs = Event.objects.filter(status="published").order_by("start_datetime")

    # Staff can see all events
    if _is_staff_like(request.user):
        qs = Event.objects.all().order_by("-created_at")

    return render(request, "events/events_list.html", {"events": qs})


@login_required
def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)

    # Students shouldn't open draft events
    if (not _is_staff_like(request.user)) and event.status != "published":
        messages.error(request, "This event is not published.")
        return redirect("events:list")

    already_registered = EventRegistration.objects.filter(event=event, user=request.user).exists()
    reg_count = event.registrations.count()

    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
            "already_registered": already_registered,
            "reg_count": reg_count,
            "is_staff_like": _is_staff_like(request.user),
        },
    )


@login_required
def event_create_view(request):
    if not _is_staff_like(request.user):
        messages.error(request, "Only staff/admin can create events.")
        return redirect("events:list")

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Event created successfully ✅")
            return redirect("events:detail", pk=obj.pk)
    else:
        form = EventForm()

    return render(request, "events/event_form.html", {"form": form})


@login_required
def event_register_view(request, pk):
    # Only students should register
    if request.user.role != User.Role.STUDENT:
        messages.error(request, "Only students can register for events.")
        return redirect("events:detail", pk=pk)

    event = get_object_or_404(Event, pk=pk, status="published")

    # close registration after event started
    if event.start_datetime <= timezone.now():
        messages.error(request, "Registration closed. This event already started.")
        return redirect("events:detail", pk=pk)

    # prevent duplicates
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
    else:
        # prefill email if available
        form = EventRegistrationForm(
            initial={
                "email": getattr(request.user, "email", "") or "",
                "full_name": getattr(request.user, "get_full_name", lambda: "")() or request.user.username,
            }
        )

    return render(request, "events/event_register.html", {"event": event, "form": form})

@login_required
def event_registrations_view(request, pk):
    # Staff/Admin only
    if request.user.role not in [User.Role.STAFF, User.Role.ADMIN]:
        messages.error(request, "You are not allowed to view event registrations.")
        return redirect("events:list")

    event = get_object_or_404(Event, pk=pk)

    regs = (
        EventRegistration.objects
        .filter(event=event)
        .select_related("user")
        .order_by("-registered_at")
    )

    context = {
        "event": event,
        "regs": regs,
        "total_regs": regs.count(),
    }
    return render(request, "events/event_registrations.html", context)

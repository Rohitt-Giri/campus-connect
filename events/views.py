from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

import csv
from django.http import HttpResponse
from accounts.models import User
from audit.utils import log_action
from notifications.utils import notify
from payments.models import PaymentProof

from events.email_utils import send_event_registration_email
from .forms import EventForm, EventRegistrationForm
from .models import Event, EventRegistration


def _staff_or_admin(user):
    if not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    return getattr(user, "role", None) in [User.Role.STAFF, User.Role.ADMIN]


@login_required
def events_list_view(request):
    event_type = (request.GET.get("type") or "all").strip()

    # Special filters for staff/admin
    if event_type == "drafts" and _staff_or_admin(request.user):
        events = Event.objects.filter(status="draft", is_active=True).order_by("-created_at")
    elif event_type == "archived" and _staff_or_admin(request.user):
        events = Event.objects.filter(is_active=False).order_by("-archived_at")
    else:
        events = Event.objects.filter(status="published", is_active=True).order_by("start_datetime")

    q = (request.GET.get("q") or "").strip()

    if q:
        events = events.filter(
            Q(title__icontains=q) | Q(location__icontains=q)
        ).order_by("start_datetime")

    if event_type == "free":
        events = events.filter(is_paid=False)
    elif event_type == "paid":
        events = events.filter(is_paid=True)

    paginator = Paginator(events, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "events/events_list.html", {
        "events": page_obj,
        "page_obj": page_obj,
        "q": q,
        "event_type": event_type,
    })


@login_required
def event_create_view(request):
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

            if will_publish and not getattr(event, "published_at", None):
                event.published_at = now

            if getattr(event, "is_active", None) is None:
                event.is_active = True

            event.save()

            if will_publish and not getattr(event, "notified_at", None):
                students = User.objects.filter(
                    role=User.Role.STUDENT,
                    is_active=True,
                    is_approved=True
                ).only("id")

                for student in students:
                    try:
                        notify(
                            student,
                            title="New event published ✅",
                            message=f"{event.title} is now available. Tap to view & register.",
                            url=reverse("events:detail", kwargs={"pk": event.id}),
                            category="events",
                        )
                    except Exception as e:
                        print(f"[NOTIFY ERROR] Event publish notify failed: {e}")

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
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            updated = form.save(commit=False)

            if updated.status == "published" and not updated.published_at:
                updated.published_at = timezone.now()

            updated.save()

            messages.success(request, "Event updated ✅")
            return redirect("events:detail", pk=event.pk)

        messages.error(request, "Please fix the errors below.")
    else:
        form = EventForm(instance=event)

    return render(request, "events/event_form.html", {"form": form, "is_edit": True, "event": event})


@login_required
def event_detail_view(request, pk):
    if _staff_or_admin(request.user):
        event = get_object_or_404(Event, pk=pk)
    else:
        event = get_object_or_404(Event, pk=pk, status="published", is_active=True)

    registration = None
    payment_proof = None
    is_registered = False

    if request.user.is_authenticated:
        try:
            registration = EventRegistration.objects.get(event=event, user=request.user)
            is_registered = True
            # Get payment proof if exists
            payment_proof = getattr(registration, "payment_proof", None)
        except EventRegistration.DoesNotExist:
            pass

    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
            "is_registered": is_registered,
            "already_registered": is_registered,
            "registration": registration,
            "payment_proof": payment_proof,
        },
    )


@login_required
def event_register_view(request, pk):
    event = get_object_or_404(Event, pk=pk, status="published", is_active=True)

    if EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.info(request, "You are already registered for this event.")
        return redirect("events:detail", pk=event.pk)

    if request.method == "POST":
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.event = event
            reg.user = request.user
            reg.save()

            try:
                send_event_registration_email(reg)
            except Exception as e:
                print(f"[EMAIL ERROR] Registration email failed: {e}")

            # In-app notification
            try:
                notify(
                    user=request.user,
                    title="Event registration confirmed ✅",
                    message=f"You registered for '{event.title}'.",
                    url=f"/events/{event.pk}/",
                    category="events",
                )
            except Exception as e:
                print(f"[NOTIFY ERROR] Registration notification failed: {e}")

            messages.success(request, "Registration submitted successfully ✅")

            if event.is_paid:
                return redirect("payments:submit", registration_id=reg.id)

            return redirect("events:detail", pk=event.pk)
    else:
        initial = {
            "full_name": request.user.get_full_name() if hasattr(request.user, "get_full_name") else "",
            "email": getattr(request.user, "email", ""),
        }
        form = EventRegistrationForm(initial=initial)

    return render(
        request,
        "events/event_register.html",
        {
            "event": event,
            "form": form,
        },
    )


@login_required
def event_registrations_view(request, pk):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)

    registrations = event.registrations.select_related("user").all()

    q = (request.GET.get("q") or "").strip()
    payment_status = (request.GET.get("payment_status") or "all").strip()

    if q:
        registrations = registrations.filter(
            Q(full_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q) |
            Q(user__username__icontains=q)
        )

    proofs_qs = PaymentProof.objects.filter(registration__event=event).select_related(
        "registration",
        "verified_by"
    )

    proof_map = {proof.registration_id: proof for proof in proofs_qs}

    rows = []
    for reg in registrations:
        proof = proof_map.get(reg.id)

        if event.is_paid:
            if payment_status == "pending":
                if not proof or proof.status != "pending":
                    continue
            elif payment_status == "approved":
                if not proof or proof.status != "approved":
                    continue
            elif payment_status == "rejected":
                if not proof or proof.status != "rejected":
                    continue
            elif payment_status == "not_submitted":
                if proof:
                    continue

        rows.append({
            "registration": reg,
            "payment_proof": proof,
        })

    paginator = Paginator(rows, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "events/event_registrations.html",
        {
            "event": event,
            "rows": page_obj,
            "page_obj": page_obj,
            "q": q,
            "payment_status": payment_status,
        },
    )


@login_required
def event_registrations_export_csv_view(request, pk):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)

    registrations = event.registrations.select_related("user").all()

    proofs = PaymentProof.objects.filter(registration__event=event)
    proof_map = {p.registration_id: p for p in proofs}

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="event_{event.id}_registrations.csv"'

    writer = csv.writer(response)

    writer.writerow([
        "Full Name",
        "Username",
        "Email",
        "Phone",
        "Registered At",
        "Payment Status"
    ])

    for reg in registrations:
        proof = proof_map.get(reg.id)

        if event.is_paid:
            payment_status = proof.status if proof else "not_submitted"
        else:
            payment_status = "free"

        writer.writerow([
            reg.full_name or reg.user.username,
            reg.user.username,
            reg.email or "",
            reg.phone or "",
            reg.registered_at.strftime("%Y-%m-%d %H:%M"),
            payment_status
        ])

    return response

@login_required
def event_archive_confirm_view(request, pk):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)
    return render(request, "events/event_archive_confirm.html", {"event": event})


@require_POST
@login_required
def event_archive_view(request, pk):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    event = get_object_or_404(Event, pk=pk)

    event.is_active = False
    event.archived_at = timezone.now()
    event.save(update_fields=["is_active", "archived_at"])

    try:
        log_action(
            actor=request.user,
            action="EVENT_UPDATE",
            target=event,
            message=f"Archived event: {event.title}",
            request=request,
        )
    except Exception:
        pass

    messages.success(request, "Event archived successfully.")
    return redirect("events:list")
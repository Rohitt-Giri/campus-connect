from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from audit.utils import log_action
from accounts.models import User
from events.models import EventRegistration
from .models import PaymentProof
from payments.email_utils import send_payment_received_email, send_payment_status_email


def _staff_or_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role in [User.Role.STAFF, User.Role.ADMIN])


def _ensure_db_required_defaults(proof: PaymentProof, event_price=None):
    # Your model already has defaults, but keep this bulletproof.
    if not proof.gateway:
        proof.gateway = "esewa"
    if proof.amount is None:
        proof.amount = event_price if event_price is not None else 0
    if not proof.currency:
        proof.currency = "NPR"
    if proof.staff_note is None:
        proof.staff_note = ""
    if not proof.txn_id:
        proof.txn_id = "manual"
    if not proof.submitted_at:
        proof.submitted_at = timezone.now()
    proof.updated_at = timezone.now()


def _set_verified_fields(proof: PaymentProof, user):
    proof.verified_by = user
    proof.verified_at = timezone.now()


@login_required
def payment_submit_view(request, registration_id):
    reg = get_object_or_404(
        EventRegistration.objects.select_related("event", "user"),
        id=registration_id,
        user=request.user
    )
    event = reg.event

    if not event.is_paid:
        messages.info(request, "This event does not require payment.")
        return redirect("events:detail", pk=event.id)

    proof = getattr(reg, "payment_proof", None)

    if request.method == "POST":
        img = request.FILES.get("proof_image")

        if not img:
            messages.error(request, "Please upload your payment screenshot.")
            return render(request, "payments/payment_submit.html", {
                "registration": reg,
                "event": event,
                "proof": proof,
            })

        if proof:
            proof.proof_image = img
            proof.status = "pending"
            proof.updated_at = timezone.now()
            _ensure_db_required_defaults(proof, event_price=getattr(event, "price", 0))
            proof.save()
        else:
            proof = PaymentProof.objects.create(
                registration=reg,
                proof_image=img,
                gateway="esewa",
                amount=getattr(event, "price", 0),
                currency="NPR",
                staff_note="",
                txn_id="manual",
                status="pending",
                submitted_at=timezone.now(),
                updated_at=timezone.now(),
            )

        # ✅ Email: student gets "we received your payment proof"
        email_sent = send_payment_received_email(proof)

        log_action(
            request=request,
            actor=request.user,
            action="PAYMENT_SUBMIT",
            message=f"Submitted payment proof for {reg.user.username} / {event.title}"
                    + (" (email sent)" if email_sent else " (no email)"),
            target=proof,
            metadata={
                "registration_id": reg.id,
                "event": event.title,
                "amount": str(getattr(proof, "amount", "")),
                "email_sent": email_sent,
            }
        )

        messages.success(request, "Payment proof submitted ✅ Waiting for verification.")
        return redirect("events:detail", pk=event.id)

    return render(request, "payments/payment_submit.html", {
        "registration": reg,
        "event": event,
        "proof": proof,
    })


@login_required
def staff_payments_list_view(request):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    status = (request.GET.get("status") or request.GET.get("tab") or "pending").strip().lower()
    if status not in {"pending", "approved", "rejected"}:
        status = "pending"

    q = (request.GET.get("q") or "").strip()

    payments = (
        PaymentProof.objects
        .select_related("registration", "registration__event", "registration__user", "verified_by")
        .filter(status__iexact=status)
        .order_by("-submitted_at")
    )

    if q:
        payments = payments.filter(
            Q(registration__event__title__icontains=q) |
            Q(registration__user__username__icontains=q) |
            Q(registration__user__email__icontains=q)
        )

    counts = {
        "pending": PaymentProof.objects.filter(status__iexact="pending").count(),
        "approved": PaymentProof.objects.filter(status__iexact="approved").count(),
        "rejected": PaymentProof.objects.filter(status__iexact="rejected").count(),
    }

    return render(request, "payments/staff_payments_list.html", {
        "proofs": payments,
        "status": status,
        "q": q,
        "counts": counts,
    })


@login_required
def staff_payment_review_view(request, proof_id):
    if not _staff_or_admin(request.user):
        messages.error(request, "Not authorized.")
        return redirect("core:landing")

    proof = get_object_or_404(
        PaymentProof.objects.select_related("registration__event", "registration__user"),
        id=proof_id
    )

    if request.method == "POST":
        action = (request.POST.get("action") or "").strip().lower()
        note = (request.POST.get("staff_note") or "").strip()

        if action == "approve":
            proof.status = "approved"
        elif action == "reject":
            proof.status = "rejected"
        else:
            messages.error(request, "Invalid action.")
            return redirect("payments:staff_review", proof_id=proof.id)

        proof.staff_note = note
        _set_verified_fields(proof, request.user)
        _ensure_db_required_defaults(proof, event_price=getattr(proof.registration.event, "price", 0))
        proof.save()

        # ✅ Email: student gets approved/rejected message
        email_sent = send_payment_status_email(proof)

        log_action(
            request=request,
            actor=request.user,
            action="PAYMENT_APPROVE" if proof.status == "approved" else "PAYMENT_REJECT",
            message=f"{'Approved' if proof.status == 'approved' else 'Rejected'} payment proof #{proof.id}"
                    + (" (email sent)" if email_sent else " (no email)"),
            target=proof,
            metadata={
                "status": proof.status,
                "email_sent": email_sent,
                "student": proof.registration.user.username,
                "event": proof.registration.event.title,
                "amount": str(getattr(proof, "amount", "")),
                "note": note,
                "flow": "staff_payment_review_view",
            }
        )

        messages.success(request, f"Payment {proof.get_status_display()} ✅")
        return redirect("payments:staff_list")

    return render(request, "payments/staff_payment_review.html", {"proof": proof})


@login_required
def staff_payment_action_view(request, proof_id):
    """
    Optional quick action endpoint (if you keep it).
    """
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    if request.method != "POST":
        return redirect("payments:staff_list")

    proof = get_object_or_404(
        PaymentProof.objects.select_related("registration__event", "registration__user"),
        id=proof_id
    )

    action = (request.POST.get("action") or "").strip().lower()
    note = (request.POST.get("staff_note") or "").strip()

    if action not in {"approve", "reject"}:
        messages.error(request, "Invalid action.")
        return redirect(request.META.get("HTTP_REFERER", "/payments/staff/?status=pending"))

    proof.status = "approved" if action == "approve" else "rejected"
    proof.staff_note = note
    _set_verified_fields(proof, request.user)
    _ensure_db_required_defaults(proof, event_price=getattr(proof.registration.event, "price", 0))
    proof.save()

    email_sent = send_payment_status_email(proof)

    log_action(
        request=request,
        actor=request.user,
        action="PAYMENT_APPROVE" if proof.status == "approved" else "PAYMENT_REJECT",
        message=f"{'Approved' if proof.status == 'approved' else 'Rejected'} payment proof #{proof.id}"
                + (" (email sent)" if email_sent else " (no email)"),
        target=proof,
        metadata={
            "status": proof.status,
            "email_sent": email_sent,
            "student": proof.registration.user.username,
            "event": proof.registration.event.title,
            "amount": str(getattr(proof, "amount", "")),
            "note": note,
            "flow": "staff_payment_action_view",
        }
    )

    messages.success(request, "Payment approved ✅" if proof.status == "approved" else "Payment rejected ❌")
    return redirect(request.META.get("HTTP_REFERER", "/payments/staff/?status=pending"))
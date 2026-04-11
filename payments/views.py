import uuid
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from audit.utils import log_action
from accounts.models import User
from events.models import EventRegistration
from .models import PaymentProof
from .esewa import build_esewa_payment_form_data, verify_esewa_payment
from payments.email_utils import send_payment_received_email, send_payment_status_email

from django.conf import settings


def _staff_or_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role in [User.Role.STAFF, User.Role.ADMIN])


def _set_verified_fields(proof, user):
    proof.verified_by = user
    proof.verified_at = timezone.now()


# ==========================================================
# PAYMENT PAGE
# ==========================================================
@login_required
def payment_submit_view(request, registration_id):
    reg = get_object_or_404(
        EventRegistration.objects.select_related("event", "user"),
        id=registration_id,
        user=request.user,
    )
    event = reg.event

    if not event.is_paid:
        messages.info(request, "This event does not require payment.")
        return redirect("events:detail", pk=event.id)

    proof = getattr(reg, "payment_proof", None)

    # Generate eSewa form data
    txn_uuid = f"CC-{reg.id}-{uuid.uuid4().hex[:8]}"

    success_url = request.build_absolute_uri(reverse("payments:esewa_success"))
    failure_url = request.build_absolute_uri(
        reverse("payments:esewa_failure", kwargs={"registration_id": reg.id})
    )

    esewa_form = build_esewa_payment_form_data(
        amount=float(event.price),
        transaction_uuid=txn_uuid,
        success_url=success_url,
        failure_url=failure_url,
    )

    # Save/update PaymentProof
    if proof:
        if proof.status != "approved":
            proof.transaction_uuid = txn_uuid
            proof.gateway = "esewa"
            proof.amount = event.price
            proof.total_amount = event.price
            proof.updated_at = timezone.now()
            proof.save()
    else:
        proof = PaymentProof(
            registration=reg,
            gateway="esewa",
            amount=event.price,
            total_amount=event.price,
            currency="NPR",
            transaction_uuid=txn_uuid,
            txn_id=txn_uuid,
            status="pending",
            submitted_at=timezone.now(),
            updated_at=timezone.now(),
            # Ensure all NOT NULL fields have values
            khalti_pidx="",
            khalti_transaction_id="",
            esewa_ref_id="",
            product_code="EPAYTEST",
            staff_note="",
            remarks="",
            signature="",
            signed_field_names="",
            transaction_code="",
            ref_id="",
            raw_request_payload="",
            raw_response_payload="",
            raw_status_payload="",
        )
        proof.save()

    return render(request, "payments/payment_submit.html", {
        "registration": reg,
        "event": event,
        "proof": proof,
        "esewa_form": esewa_form,
    })


# ==========================================================
# eSEWA SUCCESS CALLBACK
# ==========================================================
@login_required
def esewa_success_view(request):
    encoded_data = request.GET.get("data", "")

    if not encoded_data:
        messages.error(request, "Invalid payment response from eSewa.")
        return redirect("student:dashboard")

    result = verify_esewa_payment(encoded_data)

    if not result["success"]:
        messages.error(request, f"Payment verification failed: {result.get('error', 'Unknown error')}")
        return redirect("student:dashboard")

    payment_data = result["data"]
    txn_uuid = payment_data.get("transaction_uuid", "")
    txn_code = payment_data.get("transaction_code", "")

    # Find proof by transaction_uuid
    try:
        proof = PaymentProof.objects.select_related(
            "registration__event", "registration__user"
        ).get(transaction_uuid=txn_uuid)
    except PaymentProof.DoesNotExist:
        messages.error(request, "Payment record not found. Please contact support.")
        return redirect("student:dashboard")

    reg = proof.registration
    event = reg.event

    # Auto-approve
    proof.status = "approved"
    proof.gateway = "esewa"
    proof.transaction_code = txn_code
    proof.ref_id = payment_data.get("ref_id", txn_code)
    proof.esewa_ref_id = txn_code
    proof.signature = payment_data.get("signature", "")
    proof.signed_field_names = payment_data.get("signed_field_names", "")
    proof.txn_id = txn_code
    proof.verified_at = timezone.now()
    proof.staff_note = "Auto-verified via eSewa gateway."
    proof.updated_at = timezone.now()
    proof.raw_response_payload = json.dumps(result.get("raw_response", {}))
    proof.save()

    try:
        send_payment_status_email(proof)
    except Exception:
        pass

    log_action(
        request=request,
        actor=request.user,
        action="PAYMENT_APPROVE",
        message=f"eSewa payment verified for {event.title} (ref: {txn_code})",
        target=proof,
        metadata={
            "transaction_uuid": txn_uuid,
            "transaction_code": txn_code,
            "amount": str(payment_data.get("total_amount", "")),
            "gateway": "esewa",
            "auto_verified": True,
        },
    )

    messages.success(request, "Payment successful! Your registration is confirmed. ✅")
    return redirect("events:detail", pk=event.id)


# ==========================================================
# eSEWA FAILURE CALLBACK
# ==========================================================
@login_required
def esewa_failure_view(request, registration_id):
    messages.warning(request, "Payment was not completed. You can try again.")
    return redirect("payments:submit", registration_id=registration_id)


# ==========================================================
# STAFF VIEWS
# ==========================================================
@login_required
def staff_payments_list_view(request):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    status = (request.GET.get("status") or request.GET.get("tab") or "all").strip().lower()
    if status not in {"all", "pending", "approved", "rejected"}:
        status = "pending"

    q = (request.GET.get("q") or "").strip()

    payments = (
        PaymentProof.objects
        .select_related("registration", "registration__event", "registration__user", "verified_by")
        .order_by("-submitted_at")
    )

    if status != "all":
        payments = payments.filter(status__iexact=status)

    if q:
        payments = payments.filter(
            Q(registration__event__title__icontains=q) |
            Q(registration__user__username__icontains=q) |
            Q(registration__user__email__icontains=q)
        )

    counts = {
        "all": PaymentProof.objects.count(),
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
        proof.updated_at = timezone.now()
        proof.save()

        try:
            send_payment_status_email(proof)
        except Exception:
            pass

        log_action(
            request=request,
            actor=request.user,
            action="PAYMENT_APPROVE" if proof.status == "approved" else "PAYMENT_REJECT",
            message=f"{'Approved' if proof.status == 'approved' else 'Rejected'} payment #{proof.id}",
            target=proof,
            metadata={"status": proof.status, "gateway": proof.gateway},
        )

        messages.success(request, f"Payment {proof.get_status_display()} ✅")
        return redirect("payments:staff_list")

    return render(request, "payments/staff_payment_review.html", {"proof": proof})


@login_required
def staff_payment_action_view(request, proof_id):
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
    proof.updated_at = timezone.now()
    proof.save()

    try:
        send_payment_status_email(proof)
    except Exception:
        pass

    messages.success(request, "Payment approved ✅" if proof.status == "approved" else "Payment rejected ❌")
    return redirect(request.META.get("HTTP_REFERER", "/payments/staff/?status=pending"))


@login_required
def student_payments_list_view(request):
    paid_regs = []
    pending_count = approved_count = rejected_count = 0

    regs_qs = EventRegistration.objects.select_related("event", "user").filter(
        user=request.user,
        event__is_paid=True
    ).order_by("-registered_at")

    proof_map = {}
    proofs = PaymentProof.objects.select_related("registration", "registration__event").filter(
        registration__user=request.user
    ).order_by("-id")

    for p in proofs:
        if p.registration_id not in proof_map:
            proof_map[p.registration_id] = p

    pending_count = sum(1 for p in proof_map.values() if p.status == "pending")
    approved_count = sum(1 for p in proof_map.values() if p.status == "approved")
    rejected_count = sum(1 for p in proof_map.values() if p.status == "rejected")

    for reg in regs_qs:
        proof = proof_map.get(reg.id)
        paid_regs.append({
            "registration": reg,
            "event": reg.event,
            "proof": proof,
            "has_proof": proof is not None,
            "status": proof.status if proof else "not_submitted",
        })

    return render(request, "payments/student_payments_list.html", {
        "paid_regs": paid_regs,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "now": timezone.now(),
    })

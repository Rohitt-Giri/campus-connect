from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from events.models import EventRegistration
from .models import PaymentProof


def _staff_or_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role in [User.Role.STAFF, User.Role.ADMIN])


def _ensure_db_required_defaults(proof: PaymentProof, event_price=None):
    """
    Your existing MySQL table has NOT NULL columns like:
    gateway, amount, currency, staff_note, txn_id, updated_at
    This ensures they NEVER stay NULL (even for older rows).
    """
    if not getattr(proof, "gateway", None):
        proof.gateway = "esewa"

    if getattr(proof, "amount", None) is None:
        proof.amount = event_price if event_price is not None else 0

    if not getattr(proof, "currency", None):
        proof.currency = "NPR"

    # staff_note is NOT NULL in your DB, so keep empty string not NULL
    if getattr(proof, "staff_note", None) is None:
        proof.staff_note = ""

    # txn_id is NOT NULL in your DB
    if not getattr(proof, "txn_id", None):
        proof.txn_id = "manual"

    # submitted_at + updated_at are NOT NULL in your DB
    if getattr(proof, "submitted_at", None) is None:
        proof.submitted_at = timezone.now()

    proof.updated_at = timezone.now()


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
            if img:
                proof.proof_image = img
                proof.status = "pending"
                proof.updated_at = timezone.now()
                proof.save()

        else:
            PaymentProof.objects.create(
                registration=reg,
                proof_image=img,
                gateway="esewa",
                amount=event.price,
                currency="NPR",
                staff_note="",
                txn_id="manual",
                status="pending",
                submitted_at=timezone.now(),
                updated_at=timezone.now(),
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
        messages.error(request, "Not authorized.")
        return redirect("core:landing")

    status = request.GET.get("status", "pending")
    q = (request.GET.get("q") or "").strip()

    proofs = PaymentProof.objects.select_related(
        "registration__event",
        "registration__user",
        "reviewed_by",
    ).order_by("-submitted_at", "-id")

    if status in ["pending", "approved", "rejected"]:
        proofs = proofs.filter(status=status)

    if q:
        proofs = proofs.filter(
            Q(registration__user__username__icontains=q) |
            Q(registration__user__email__icontains=q) |
            Q(registration__event__title__icontains=q) |
            Q(txn_id__icontains=q)
        )

    return render(request, "payments/staff_payments_list.html", {
        "proofs": proofs,
        "status": status,
        "q": q,
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
        action = request.POST.get("action")
        note = (request.POST.get("staff_note") or "").strip()

        if action == "approve":
            proof.status = "approved"
        elif action == "reject":
            proof.status = "rejected"
        else:
            messages.error(request, "Invalid action.")
            return redirect("payments:staff_review", proof_id=proof.id)

        # staff_note is NOT NULL in DB
        proof.staff_note = note

        proof.reviewed_by = request.user
        proof.reviewed_at = timezone.now()

        _ensure_db_required_defaults(proof, event_price=getattr(proof.registration.event, "price", 0))
        proof.save()

        messages.success(request, f"Payment {proof.get_status_display()} ✅")
        return redirect("payments:staff_list")

    return render(request, "payments/staff_payment_review.html", {"proof": proof})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from events.models import EventRegistration
from .forms import PaymentProofForm
from .models import PaymentProof


@login_required
def payment_submit_view(request, registration_id):
    registration = get_object_or_404(EventRegistration, id=registration_id)

    # Only the same student can upload payment proof for their registration
    if request.user != registration.user:
        messages.error(request, "You are not allowed to upload payment for this registration.")
        return redirect("events:detail", pk=registration.event.pk)

    # Event must be paid to upload payment
    if not getattr(registration.event, "is_paid", False):
        messages.info(request, "This event does not require payment.")
        return redirect("events:detail", pk=registration.event.pk)

    payment_obj, _ = PaymentProof.objects.get_or_create(registration=registration)

    if request.method == "POST":
        form = PaymentProofForm(request.POST, request.FILES, instance=payment_obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = "pending"  # always pending on upload/update
            obj.save()
            messages.success(request, "Payment proof uploaded. Waiting for approval ✅")
            return redirect("events:detail", pk=registration.event.pk)
    else:
        form = PaymentProofForm(instance=payment_obj)

    return render(request, "payments/payment_submit.html", {
        "form": form,
        "registration": registration,
        "event": registration.event,
        "payment": payment_obj,
    })


@login_required
def staff_payments_list_view(request):
    # only staff/admin
    if request.user.role not in [User.Role.STAFF, User.Role.ADMIN]:
        messages.error(request, "Unauthorized.")
        return redirect("core:landing")

    payments = PaymentProof.objects.select_related(
        "registration", "registration__event", "registration__user"
    ).order_by("-created_at")

    return render(request, "payments/staff_payments_list.html", {"payments": payments})


@login_required
def staff_payment_decide_view(request, pk, action):
    if request.user.role not in [User.Role.STAFF, User.Role.ADMIN]:
        messages.error(request, "Unauthorized.")
        return redirect("core:landing")

    payment = get_object_or_404(PaymentProof, pk=pk)

    if action not in ["approve", "reject"]:
        messages.error(request, "Invalid action.")
        return redirect("payments:staff_list")

    payment.status = "approved" if action == "approve" else "rejected"
    payment.reviewed_by = request.user
    payment.reviewed_at = timezone.now()
    payment.save()

    messages.success(request, f"Payment {payment.status} ✅")
    return redirect("payments:staff_list")

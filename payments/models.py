from django.conf import settings
from django.db import models
from django.utils import timezone
from events.models import EventRegistration


class PaymentProof(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    registration = models.OneToOneField(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name="payment_proof",
        db_column="registration_id"
    )

    # 🔥 EXACT DB FIELDS (required by MySQL)
    gateway = models.CharField(max_length=30, default="esewa")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="NPR")
    staff_note = models.TextField(default="", blank=True)
    txn_id = models.CharField(max_length=80, default="manual")

    proof_image = models.ImageField(upload_to="payments/proofs/", db_column="proof_image")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    submitted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="verified_by_id",
        related_name="verified_payments"
    )

    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, default="")

    class Meta:
        db_table = "payments_paymentproof"

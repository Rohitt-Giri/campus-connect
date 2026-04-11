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

    # Core payment fields
    gateway = models.CharField(max_length=30, default="esewa")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="NPR")
    staff_note = models.TextField(default="", blank=True)
    txn_id = models.CharField(max_length=80, default="", blank=True)

    # Legacy proof image (optional - kept for backward compat)
    proof_image = models.ImageField(
        upload_to="payments/proofs/",
        db_column="proof_image",
        blank=True,
        null=True,
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    submitted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="verified_by_id",
        related_name="verified_payments"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        db_column="reviewed_by_id",
        related_name="reviewed_payments"
    )

    remarks = models.TextField(blank=True, default="")

    # Khalti fields (exist in DB from previous migration)
    khalti_pidx = models.CharField(max_length=100, blank=True, default="")
    khalti_transaction_id = models.CharField(max_length=100, blank=True, default="")

    # eSewa fields (exist in DB)
    esewa_ref_id = models.CharField(max_length=100, blank=True, default="")
    product_code = models.CharField(max_length=50, blank=True, default="")
    product_delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    product_service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    raw_request_payload = models.TextField(blank=True, default="")
    raw_response_payload = models.TextField(blank=True, default="")
    raw_status_payload = models.TextField(blank=True, default="")
    ref_id = models.CharField(max_length=100, blank=True, default="")
    signature = models.CharField(max_length=255, blank=True, default="")
    signed_field_names = models.CharField(max_length=255, blank=True, default="")
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_code = models.CharField(max_length=100, blank=True, default="")
    transaction_uuid = models.CharField(max_length=100, blank=True, default="")

    class Meta:
        db_table = "payments_paymentproof"
        managed = False  # Don't let Django try to alter the table

    def __str__(self):
        return f"Payment #{self.id} - {self.status} ({self.gateway})"

from django.conf import settings
from django.db import models
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
        related_name="payment_proof"
    )

    proof_image = models.ImageField(upload_to="payments/proofs/")
    remarks = models.CharField(max_length=255, blank=True, default="")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_payments"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.registration.user} - {self.registration.event} ({self.status})"

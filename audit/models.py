from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Minimal audit log (DB-safe, simple, searchable).
    Stores: who did what, to which object, and optional details.
    """

    ACTION_CHOICES = (
        ("USER_APPROVE", "User Approved"),
        ("USER_DEACTIVATE", "User Deactivated"),
        ("USER_ACTIVATE", "User Activated"),
        ("USER_ROLE_CHANGE", "User Role Changed"),

        ("PAYMENT_APPROVE", "Payment Approved"),
        ("PAYMENT_REJECT", "Payment Rejected"),

        ("CLAIM_APPROVE", "Claim Approved"),
        ("CLAIM_REJECT", "Claim Rejected"),
        ("ITEM_RETURNED", "Item Marked Returned"),

        ("NOTICE_CREATE", "Notice Created"),
        ("NOTICE_UPDATE", "Notice Updated"),

        ("EVENT_CREATE", "Event Created"),
        ("EVENT_UPDATE", "Event Updated"),
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs"
    )

    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    message = models.CharField(max_length=255, blank=True, default="")

    # Generic target reference (no GenericForeignKey needed)
    target_model = models.CharField(max_length=80, blank=True, default="")
    target_id = models.CharField(max_length=64, blank=True, default="")
    target_label = models.CharField(max_length=255, blank=True, default="")

    # Extra info
    ip_address = models.CharField(max_length=45, blank=True, default="")
    metadata = models.JSONField(blank=True, default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_auditlog"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} by {self.actor} @ {self.created_at}"
    

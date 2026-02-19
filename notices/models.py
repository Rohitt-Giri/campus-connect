from django.conf import settings
from django.db import models


class Notice(models.Model):
    class Category(models.TextChoices):
        GENERAL = "GENERAL", "General"
        EVENT = "EVENT", "Event"
        LOST_FOUND = "LOST_FOUND", "Lost & Found"
        PAYMENT = "PAYMENT", "Payment"
        URGENT = "URGENT", "Urgent"

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="notices_created"
    )

    is_active = models.BooleanField(default=True)  # soft delete/archive
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

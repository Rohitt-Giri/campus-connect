from django.conf import settings
from django.db import models
from django.utils import timezone


class Notice(models.Model):
    class Category(models.TextChoices):
        GENERAL = "GENERAL", "General"
        EVENT = "EVENT", "Event"
        LOST_FOUND = "LOST_FOUND", "Lost & Found"
        PAYMENT = "PAYMENT", "Payment"
        URGENT = "URGENT", "Urgent"

    class Audience(models.TextChoices):
        ALL = "ALL", "All Users"
        STUDENTS = "STUDENTS", "Students"
        STAFF = "STAFF", "Staff"

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)

    # ✅ New
    audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.ALL)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="notices_created"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    published_at = models.DateTimeField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
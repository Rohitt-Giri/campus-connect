from django.conf import settings
from django.db import models


class Item(models.Model):
    class ItemType(models.TextChoices):
        LOST = "lost", "Lost"
        FOUND = "found", "Found"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RETURNED = "returned", "Returned"
        CLOSED = "closed", "Closed"

    item_type = models.CharField(max_length=10, choices=ItemType.choices, default=ItemType.LOST)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    date_happened = models.DateField(null=True, blank=True)

    image = models.ImageField(upload_to="lostfound/", null=True, blank=True)

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lostfound_items",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_item_type_display()}: {self.title}"


class Claim(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="claims")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lostfound_claims")

    # Student claim form fields
    full_name = models.CharField(max_length=150, default="", blank=True)
    phone = models.CharField(max_length=30, default="", blank=True)
    email = models.EmailField(default="", blank=True)
    proof_message = models.TextField(blank=True, default="")

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lostfound_claims_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("item", "student")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Claim({self.student}) -> {self.item}"

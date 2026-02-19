from django.conf import settings
from django.db import models


class LostFoundItem(models.Model):
    TYPE_CHOICES = (
        ("lost", "Lost"),
        ("found", "Found"),
    )

    STATUS_CHOICES = (
        ("open", "Open"),
        ("returned", "Returned"),
    )

    # matches your DB columns
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)   # longtext in DB
    location = models.CharField(max_length=200, blank=True)
    date_happened = models.DateField(null=True, blank=True)
    image = models.CharField(max_length=100, blank=True)  # varchar in DB (NOT ImageField)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="created_by_id",
        related_name="lostfound_items",
    )
    type = models.CharField(max_length=10, blank=True)  # column exists in your DB

    class Meta:
        db_table = "lostfound_item"

    def __str__(self):
        return f"{self.item_type} - {self.title}"


class ClaimRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    # matches your DB columns
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50)
    email = models.CharField(max_length=255)
    proof_message = models.TextField()  # your DB uses proof_message, not message
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="reviewed_by_id",
        related_name="lostfound_claims_reviewed",
    )

    created_at = models.DateTimeField()

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="student_id",
        related_name="lostfound_claims",
    )

    item = models.ForeignKey(
        LostFoundItem,
        on_delete=models.CASCADE,
        db_column="item_id",
        related_name="claims",
    )

    class Meta:
        db_table = "lostfound_claim"

    def __str__(self):
        return f"{self.full_name} -> {self.item_id} ({self.status})"

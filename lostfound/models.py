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

    # DB columns
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    date_happened = models.DateField(null=True, blank=True)

    # IMPORTANT:
    # DB column is varchar, but we can still map it with ImageField using db_column="image"
    # because ImageField stores the file path as a string in DB.
    image = models.ImageField(
        upload_to="lostfound/items/",
        blank=True,
        null=True,
        db_column="image",
        max_length=255,
    )

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="created_by_id",
        related_name="lostfound_items",
    )

    # If your DB truly has a "type" column and you must keep it, keep it:
    # Otherwise, remove it to avoid confusion with item_type.
    type = models.CharField(max_length=10, blank=True)

    class Meta:
        db_table = "lostfound_item"

    def __str__(self):
        return f"{self.item_type} - {self.title}"

    @property
    def image_url(self):
        if not self.image:
            return ""
        try:
            return self.image.url
        except Exception:
            path = str(self.image).lstrip("/")
            return f"{settings.MEDIA_URL}{path}"

    


class ClaimRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    # DB-safe (won’t block migrations)
    full_name = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.CharField(max_length=255, blank=True, default="")
    proof_message = models.TextField(blank=True, default="")
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

    created_at = models.DateTimeField(auto_now_add=True)

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
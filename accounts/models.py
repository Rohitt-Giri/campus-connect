from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        STAFF = "STAFF", "Staff"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        db_column="user_id",
    )

    photo = models.ImageField(upload_to="profiles/", null=True, blank=True, max_length=255)

    # ✅ General (used in UI)
    full_name = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    bio = models.TextField(blank=True, default="")

    # student
    program = models.CharField(max_length=120, blank=True, default="")
    semester = models.CharField(max_length=30, blank=True, default="")
    student_id = models.CharField(max_length=50, blank=True, default="")

    # staff
    department = models.CharField(max_length=120, blank=True, default="")
    designation = models.CharField(max_length=120, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "accounts_userprofile"

    def __str__(self):
        return f"Profile({self.user_id})"

    @property
    def avatar_letter(self):
        u = getattr(self, "user", None)
        if u and getattr(u, "username", ""):
            return u.username[:1].upper()
        return "U"
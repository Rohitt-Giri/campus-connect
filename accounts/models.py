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

    photo = models.ImageField(upload_to="profiles/", null=True, blank=True, max_length=255, db_column="photo")

    # basic
    full_name = models.CharField(max_length=255, blank=True, default="", db_column="full_name")
    phone = models.CharField(max_length=30, blank=True, default="", db_column="phone")
    bio = models.TextField(blank=True, default="", db_column="bio")

    # student
    program = models.CharField(max_length=120, blank=True, default="", db_column="program")
    semester = models.CharField(max_length=30, blank=True, default="", db_column="semester")
    student_id = models.CharField(max_length=50, blank=True, default="", db_column="student_id")

    # staff
    department = models.CharField(max_length=120, blank=True, default="", db_column="department")
    designation = models.CharField(max_length=120, blank=True, default="", db_column="designation")

    created_at = models.DateTimeField(default=timezone.now, db_column="created_at")
    updated_at = models.DateTimeField(default=timezone.now, db_column="updated_at")

    class Meta:
        db_table = "accounts_userprofile"

    def __str__(self):
        return f"Profile({self.user_id})"

    @property
    def avatar_letter(self) -> str:
        # priority: full_name -> username -> "U"
        name = (self.full_name or "").strip()
        if name:
            return name[0].upper()
        try:
            uname = (self.user.username or "").strip()
        except Exception:
            uname = ""
        return (uname[:1].upper() or "U")

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)
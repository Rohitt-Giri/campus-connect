from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    CATEGORY_CHOICES = (
        ("notices", "Notices"),
        ("events", "Events"),
        ("payments", "Payments"),
        ("lostfound", "Lost & Found"),
        ("accounts", "Accounts"),
        ("system", "System"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_column="user_id",
    )

    title = models.CharField(max_length=160)
    message = models.TextField(default="", blank=True)
    url = models.CharField(max_length=255, default="", blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="system")

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id}: {self.title}"
    
def unread_notifications(request):
    if not request.user.is_authenticated:
        return {"unread_count": 0}

    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return {"unread_count": count}
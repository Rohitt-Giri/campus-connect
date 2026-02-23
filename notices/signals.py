from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from notifications.models import Notification
from .models import Notice


def _notice_url():
    # If you have notice detail later, update this.
    try:
        return reverse("notices:list")
    except Exception:
        return "/notices/"


@receiver(post_save, sender=Notice)
def create_notifications_on_publish(sender, instance: Notice, created, **kwargs):
    """
    When notice becomes active and hasn't been notified yet:
    - set published_at (first time)
    - create Notification rows for users
    - set notified_at to prevent duplicates
    """

    if not instance.is_active:
        return

    # Set published_at only once
    if instance.published_at is None:
        instance.published_at = timezone.now()
        Notice.objects.filter(pk=instance.pk).update(published_at=instance.published_at)

    # Prevent duplicates
    if instance.notified_at:
        return

    title = (instance.title or "New Notice").strip()
    content = (instance.content or "").strip()
    msg = content[:240]  # keep short

    url = _notice_url()
    category = "notices"

    # Who gets notifications? (professional default)
    # ✅ Students + Staff (exclude admins unless you want them)
    recipients = User.objects.filter(
        is_active=True,
        role__in=[User.Role.STUDENT, User.Role.STAFF],
    ).only("id")

    now = timezone.now()
    batch = [
        Notification(
            user_id=u.id,
            title=f"📢 {title}"[:160],
            message=msg,
            url=url,
            category=category,
            is_read=False,
            created_at=now,
        )
        for u in recipients
    ]

    Notification.objects.bulk_create(batch, batch_size=1000)

    # Mark as notified
    Notice.objects.filter(pk=instance.pk).update(notified_at=timezone.now())
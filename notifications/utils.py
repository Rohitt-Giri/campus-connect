from django.utils import timezone
from .models import Notification


def notify(user, *, title: str, message: str = "", url: str = "", category: str = "system") -> bool:
    if not user:
        return False

    Notification.objects.create(
        user=user,
        title=(title or "")[:160],
        message=message or "",
        url=url or "",
        category=category or "system",
        created_at=timezone.now(),
    )
    return True
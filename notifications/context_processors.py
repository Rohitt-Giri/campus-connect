# notifications/context_processors.py

def notifications_ctx(request):
    """
    Provides unread_count to ALL templates.
    Never crash the site even if tables aren't ready yet.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"unread_count": 0}

    try:
        from .models import Notification
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
    except Exception:
        unread = 0

    return {"unread_count": unread}
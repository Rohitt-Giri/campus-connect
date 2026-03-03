# notifications/context_processors.py
def unread_notifications(request):
    # for now, keep it simple so it never crashes
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"unread_count": 0}

    try:
        from .models import Notification
        count = Notification.objects.filter(user=request.user, is_read=False).count()
    except Exception:
        # if model isn't ready yet, don't break the whole site
        count = 0

    return {"unread_count": count}
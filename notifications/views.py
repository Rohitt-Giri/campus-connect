# notifications/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notifications_list_view(request):
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "notifications/list.html", {"notifications": qs})


@login_required
@require_POST
def notifications_mark_read_view(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save(update_fields=["is_read"])
    return redirect(request.META.get("HTTP_REFERER", "notifications:list"))


@login_required
@require_POST
def notifications_mark_all_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read ✅")
    return redirect(request.META.get("HTTP_REFERER", "notifications:list"))


@login_required
def notification_go_view(request, pk):
    """
    When user clicks a notif, mark read then redirect to its URL.
    """
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    if not n.is_read:
        n.is_read = True
        n.save(update_fields=["is_read"])

    if n.url:
        return redirect(n.url)

    return redirect("notifications:list")
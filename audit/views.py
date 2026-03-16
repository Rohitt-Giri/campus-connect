from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from accounts.decorators import admin_required
from .models import AuditLog


@admin_required
def admin_audit_logs_view(request):
    logs_qs = AuditLog.objects.select_related("actor").all()

    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()

    if q:
        logs_qs = logs_qs.filter(
            Q(message__icontains=q) |
            Q(target_label__icontains=q) |
            Q(actor__username__icontains=q)
        )

    if action:
        logs_qs = logs_qs.filter(action=action)

    logs_qs = logs_qs.order_by("-created_at")

    paginator = Paginator(logs_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "audit/admin_logs.html", {
        "logs": page_obj,
        "page_obj": page_obj,
        "q": q,
        "action": action,
        "actions": AuditLog.ACTION_CHOICES,
    })
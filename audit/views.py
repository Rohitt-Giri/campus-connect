from django.db.models import Q
from django.shortcuts import render
from accounts.decorators import admin_required
from .models import AuditLog


@admin_required
def admin_audit_logs_view(request):
    logs = AuditLog.objects.select_related("actor").all()

    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()

    if q:
        logs = logs.filter(
            Q(message__icontains=q) |
            Q(target_label__icontains=q) |
            Q(actor__username__icontains=q)
        )

    if action:
        logs = logs.filter(action=action)

    logs = logs.order_by("-created_at")[:200]

    return render(request, "audit/admin_logs.html", {
        "logs": logs,
        "q": q,
        "action": action,
        "actions": AuditLog.ACTION_CHOICES,
    })
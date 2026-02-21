from .models import AuditLog


def get_client_ip(request):
    if not request:
        return ""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def log_action(*, request=None, actor=None, action="", message="", target=None, metadata=None):
    """
    Call this anywhere:
    log_action(request=request, actor=request.user, action="USER_APPROVE", target=user, metadata={...})
    """
    if metadata is None:
        metadata = {}

    target_model = ""
    target_id = ""
    target_label = ""

    if target is not None:
        target_model = f"{target.__class__.__module__}.{target.__class__.__name__}"
        target_id = str(getattr(target, "pk", "") or "")
        # safe label for display
        target_label = str(target)[:255]

    AuditLog.objects.create(
        actor=actor,
        action=action,
        message=(message or "")[:255],
        target_model=target_model,
        target_id=target_id[:64],
        target_label=target_label,
        ip_address=get_client_ip(request),
        metadata=metadata,
    )
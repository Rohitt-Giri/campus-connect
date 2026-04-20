from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

from accounts.models import User
from .forms import ClaimRequestForm, LostFoundItemForm
from .models import ClaimRequest, LostFoundItem

from lostfound.email_utils import send_claim_status_email, send_item_returned_email
from audit.utils import log_action
try:
    from notifications.utils import notify
except Exception:
    notify = None

# If you used this somewhere else, import it (you were calling it)
try:
    from lostfound.email_utils import send_claim_received_email
except Exception:
    send_claim_received_email = None


def _staff_or_admin(user) -> bool:
    if not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    return getattr(user, "role", "") in [User.Role.STAFF, User.Role.ADMIN]


# -------------------------
# STUDENT
# -------------------------

@login_required
def items_list_view(request):
    q = (request.GET.get("q") or "").strip()
    item_type = (request.GET.get("type") or "").strip()
    status = (request.GET.get("status") or "").strip()

    # ✅ hide archived from students
    qs = LostFoundItem.objects.select_related("created_by").filter(is_archived=False)

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(location__icontains=q)
        )
    if item_type in {"lost", "found"}:
        qs = qs.filter(item_type=item_type)
    if status in {"open", "returned"}:
        qs = qs.filter(status=status)

    return render(request, "lostfound/items_list.html", {
        "items": qs.order_by("-created_at"),
        "q": q,
        "type": item_type,
        "status": status,
    })


@login_required
def item_detail_view(request, pk):
    item = get_object_or_404(
        LostFoundItem.objects.select_related("created_by"),
        pk=pk
    )

    # ✅ if archived, only staff/admin can see
    if item.is_archived and not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    already_claimed = ClaimRequest.objects.filter(item_id=item.id, student_id=request.user.id).exists()
    can_claim = (item.status == "open") and (item.created_by_id != request.user.id) and (not item.is_archived)

    claims = None
    if _staff_or_admin(request.user):
        claims = item.claims.select_related("student").all()

    return render(request, "lostfound/item_detail.html", {
        "item": item,
        "already_claimed": already_claimed,
        "can_claim": can_claim,
        "claims": claims,
    })


@login_required
def item_create_view(request):
    if request.method == "POST":
        form = LostFoundItemForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.status = "open"
            obj.created_at = timezone.now()

            # keep the legacy column "type" consistent if you still have it
            obj.type = obj.item_type

            # ✅ always start as active
            obj.is_archived = False
            obj.archived_at = None

            obj.save()
            messages.success(request, "Item posted successfully ✅")
            return redirect("lostfound:list")
    else:
        form = LostFoundItemForm()

    return render(request, "lostfound/item_form.html", {"form": form})


@login_required
def claim_create_view(request, pk):
    item = get_object_or_404(LostFoundItem, pk=pk)

    if item.is_archived:
        messages.error(request, "This item is archived and cannot be claimed.")
        return redirect("lostfound:detail", pk=item.pk)

    if item.status != "open":
        messages.error(request, "This item is already marked as returned.")
        return redirect("lostfound:detail", pk=item.pk)

    if item.created_by_id == request.user.id:
        messages.error(request, "You cannot claim your own post.")
        return redirect("lostfound:detail", pk=item.pk)

    if ClaimRequest.objects.filter(item=item, student=request.user).exists():
        messages.info(request, "You already submitted a claim for this item.")
        return redirect("lostfound:detail", pk=item.pk)

    if request.method == "POST":
        form = ClaimRequestForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.item = item
            claim.student = request.user
            claim.status = "pending"
            claim.created_at = timezone.now()
            claim.save()

            email_sent = False
            if send_claim_received_email:
                try:
                    email_sent = send_claim_received_email(claim)
                except Exception:
                    email_sent = False
                    print(f"[EMAIL ERROR] {e}")

            log_action(
                request=request,
                actor=request.user,
                action="CLAIM_SUBMIT",
                message=f"Submitted claim for item #{item.id}"
                        + (" (email sent)" if email_sent else " (no email)"),
                target=claim,
                metadata={
                    "item_id": item.id,
                    "student": request.user.username,
                    "email_sent": email_sent,
                },
            )

            messages.success(request, "Claim submitted ✅" + (" (Email sent)" if email_sent else ""))
            return redirect("lostfound:detail", pk=item.pk)
    else:
        form = ClaimRequestForm(initial={"email": request.user.email})

    return render(request, "lostfound/claim_form.html", {"form": form, "item": item})


@login_required
def my_posts_view(request):
    items = LostFoundItem.objects.filter(created_by_id=request.user.id).order_by("-created_at")
    return render(request, "lostfound/my_posts.html", {"items": items})


@login_required
def my_claims_view(request):
    claims = ClaimRequest.objects.filter(student_id=request.user.id).select_related("item").order_by("-created_at")
    return render(request, "lostfound/my_claims.html", {"claims": claims})


# -------------------------
# STAFF
# -------------------------

@never_cache
@login_required
def staff_items_view(request):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    show = (request.GET.get("show") or "").strip()  # "" | "archived"
    base = LostFoundItem.objects.select_related("created_by").annotate(
        claim_count=Count("claims")
    )

    if show == "archived":
        base = base.filter(is_archived=True)
    else:
        base = base.filter(is_archived=False)

    items = base.order_by("-created_at")

    # KPI counts (DB dynamic, responsive UI)
    total_items = items.count()
    open_count = items.filter(status="open").count()
    returned_count = items.filter(status="returned").count()

    return render(request, "lostfound/staff_items.html", {
        "items": items,
        "show": show,
        "total_items": total_items,
        "open_count": open_count,
        "returned_count": returned_count,
        "now": timezone.now(),
    })


@login_required
def staff_mark_returned_view(request, pk):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    item = get_object_or_404(LostFoundItem, pk=pk)

    if request.method == "POST":
        item.status = "returned"
        item.save(update_fields=["status"])

        to_user = item.created_by
        try:
            email_sent = send_item_returned_email(item, to_user=to_user)
        except Exception:
            email_sent = False

        log_action(
            request=request,
            actor=request.user,
            action="ITEM_MARK_RETURNED",
            message=f"Marked item #{item.id} as returned"
                    + (" (email sent)" if email_sent else " (no email)"),
            target=item,
            metadata={
                "item_id": item.id,
                "email_sent": email_sent,
                "to_user": getattr(to_user, "username", ""),
                "to_email": getattr(to_user, "email", ""),
            }
        )

        messages.success(request, "Item marked as returned ✅" + (" (Email sent)" if email_sent else ""))

    return redirect("lostfound:staff_items")


@login_required
def staff_claims_view(request):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    status = (request.GET.get("status") or "pending").strip()
    qs = ClaimRequest.objects.select_related("item", "student")

    if status in {"pending", "approved", "rejected"}:
        qs = qs.filter(status=status)

    return render(request, "lostfound/staff_claims.html", {"claims": qs.order_by("-created_at"), "status": status})


@login_required
def staff_claim_review_view(request, pk):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    claim = get_object_or_404(
        ClaimRequest.objects.select_related("item", "student"),
        pk=pk
    )

    if request.method == "POST":
        action = (request.POST.get("action") or "").strip().lower()
        if action not in {"approve", "reject"}:
            messages.error(request, "Invalid action.")
            return redirect("lostfound:staff_claims")

        claim.reviewed_by = request.user
        claim.reviewed_at = timezone.now()

        if action == "approve":
            claim.status = "approved"
            claim.save(update_fields=["status", "reviewed_by", "reviewed_at"])

            try:
                claim.item.status = "returned"
                claim.item.save(update_fields=["status"])
            except Exception:
                pass

            try:
                email_sent = send_claim_status_email(claim)
            except Exception:
                email_sent = False

            log_action(
                request=request,
                actor=request.user,
                action="CLAIM_APPROVE",
                message=f"Approved claim #{claim.id} for item #{claim.item_id}"
                        + (" (email sent)" if email_sent else " (no email)"),
                target=claim,
                metadata={
                    "claim_id": claim.id,
                    "item_id": claim.item_id,
                    "status": claim.status,
                    "email_sent": email_sent,
                    "student": getattr(getattr(claim, "student", None), "username", ""),
                    "student_email": getattr(getattr(claim, "student", None), "email", ""),
                }
            )

            messages.success(request, "Claim approved ✅ Item marked returned." + (" (Email sent)" if email_sent else ""))

            if notify:
                try:
                    notify(
                        user=claim.student,
                        title="Claim approved ✅",
                        message=f"Your claim for '{claim.item.title}' has been approved.",
                        url=f"/lostfound/my-claims/",
                        category="lostfound",
                    )
                except Exception:
                    pass

            return redirect("lostfound:staff_claims")

        # reject
        claim.status = "rejected"
        claim.save(update_fields=["status", "reviewed_by", "reviewed_at"])

        try:
            email_sent = send_claim_status_email(claim)
        except Exception:
            email_sent = False

        log_action(
            request=request,
            actor=request.user,
            action="CLAIM_REJECT",
            message=f"Rejected claim #{claim.id} for item #{claim.item_id}"
                    + (" (email sent)" if email_sent else " (no email)"),
            target=claim,
            metadata={
                "claim_id": claim.id,
                "item_id": claim.item_id,
                "status": claim.status,
                "email_sent": email_sent,
                "student": getattr(getattr(claim, "student", None), "username", ""),
                "student_email": getattr(getattr(claim, "student", None), "email", ""),
            }
        )

        messages.success(request, "Claim rejected ❌" + (" (Email sent)" if email_sent else ""))
        return redirect("lostfound:staff_claims")

    return render(request, "lostfound/staff_claim_review.html", {"claim": claim})


@login_required
def staff_item_archive_confirm(request, item_id):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    item = get_object_or_404(LostFoundItem, id=item_id)
    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or ""
    return render(request, "lostfound/staff_item_archive_confirm.html", {
        "item": item,
        "next": next_url,
    })


@login_required
@require_POST
def staff_item_archive(request, item_id):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    item = get_object_or_404(LostFoundItem, id=item_id)

    if not item.is_archived:
        item.is_archived = True
        item.archived_at = timezone.now()
        item.save(update_fields=["is_archived", "archived_at"])
        messages.success(request, f"Archived: {item.title}")
    else:
        messages.info(request, "Item is already archived.")

    back = request.POST.get("next") or request.META.get("HTTP_REFERER") or ""
    return redirect(back) if back else redirect("lostfound:staff_items")


@login_required
@require_POST
def staff_item_unarchive(request, item_id):
    if not _staff_or_admin(request.user):
        return HttpResponseForbidden("Not allowed")

    item = get_object_or_404(LostFoundItem, id=item_id)

    if item.is_archived:
        item.is_archived = False
        item.archived_at = None
        item.save(update_fields=["is_archived", "archived_at"])
        messages.success(request, f"Unarchived: {item.title}")
    else:
        messages.info(request, "Item is already active.")

    back = request.POST.get("next") or request.META.get("HTTP_REFERER") or ""
    return redirect(back) if back else redirect("lostfound:staff_items")


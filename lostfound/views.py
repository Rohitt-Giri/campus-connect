from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from .forms import ClaimRequestForm, LostFoundItemForm
from .models import ClaimRequest, LostFoundItem


def _is_staff_user(user) -> bool:
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

    qs = LostFoundItem.objects.select_related("created_by")

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
        "items": qs,
        "q": q,
        "type": item_type,
        "status": status,
    })


@login_required
def item_detail_view(request, pk):
    item = get_object_or_404(LostFoundItem.objects.select_related("created_by"), pk=pk)

    already_claimed = ClaimRequest.objects.filter(item_id=item.id, student_id=request.user.id).exists()
    can_claim = (item.status == "open") and (item.created_by_id != request.user.id)

    claims = None
    if _is_staff_user(request.user):
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
            # keep the legacy column "type" consistent
            obj.type = obj.item_type
            obj.save()
            messages.success(request, "Item posted successfully ✅")
            return redirect("lostfound:list")
    else:
        form = LostFoundItemForm()

    return render(request, "lostfound/item_form.html", {"form": form})


@login_required
def claim_create_view(request, pk):
    item = get_object_or_404(LostFoundItem, pk=pk)

    if item.status != "open":
        messages.error(request, "This item is already marked as returned.")
        return redirect("lostfound:detail", pk=item.pk)

    # prevent claiming your own post
    if item.created_by_id == request.user.id:
        messages.error(request, "You cannot claim your own post.")
        return redirect("lostfound:detail", pk=item.pk)

    # optional spam rule (one claim per user per item)
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
            messages.success(request, "Claim submitted. Staff will review it ✅")
            return redirect("lostfound:detail", pk=item.pk)
    else:
        # prefill email from account
        form = ClaimRequestForm(initial={"email": request.user.email})

    return render(request, "lostfound/claim_form.html", {"form": form, "item": item})


@login_required
def my_posts_view(request):
    items = LostFoundItem.objects.filter(created_by_id=request.user.id)
    return render(request, "lostfound/my_posts.html", {"items": items})


@login_required
def my_claims_view(request):
    claims = ClaimRequest.objects.filter(student_id=request.user.id).select_related("item")
    return render(request, "lostfound/my_claims.html", {"claims": claims})


# -------------------------
# STAFF
# -------------------------

@login_required
def staff_items_view(request):
    if not _is_staff_user(request.user):
        return HttpResponseForbidden("Not allowed")

    items = LostFoundItem.objects.all().annotate(claim_count=Count("claims")).select_related("created_by")
    return render(request, "lostfound/staff_items.html", {"items": items})


@login_required
def staff_mark_returned_view(request, pk):
    if not _is_staff_user(request.user):
        return HttpResponseForbidden("Not allowed")

    item = get_object_or_404(LostFoundItem, pk=pk)

    if request.method == "POST":
        item.status = "returned"
        item.save(update_fields=["status"])
        messages.success(request, "Item marked as returned ✅")

    return redirect("lostfound:staff_items")


@login_required
def staff_claims_view(request):
    if not _is_staff_user(request.user):
        return HttpResponseForbidden("Not allowed")

    status = (request.GET.get("status") or "pending").strip()
    qs = ClaimRequest.objects.select_related("item", "student")

    if status in {"pending", "approved", "rejected"}:
        qs = qs.filter(status=status)

    return render(request, "lostfound/staff_claims.html", {"claims": qs, "status": status})


@login_required
def staff_claim_review_view(request, pk):
    if not _is_staff_user(request.user):
        return HttpResponseForbidden("Not allowed")

    claim = get_object_or_404(ClaimRequest.objects.select_related("item", "student"), pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            claim.status = "approved"
            claim.reviewed_by = request.user
            claim.reviewed_at = timezone.now()
            claim.save(update_fields=["status", "reviewed_by", "reviewed_at"])

            claim.item.status = "returned"
            claim.item.save(update_fields=["status"])

            messages.success(request, "Claim approved ✅ Item marked returned.")
            return redirect("lostfound:staff_claims")

        if action == "reject":
            claim.status = "rejected"
            claim.reviewed_by = request.user
            claim.reviewed_at = timezone.now()
            claim.save(update_fields=["status", "reviewed_by", "reviewed_at"])
            messages.success(request, "Claim rejected ❌")
            return redirect("lostfound:staff_claims")

        messages.error(request, "Invalid action.")
        return redirect("lostfound:staff_claims")

    return render(request, "lostfound/staff_claim_review.html", {"claim": claim})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from .forms import ClaimForm, ItemForm
from .models import Claim, Item


def _is_staff(user) -> bool:
    return getattr(user, "role", None) in [User.Role.STAFF, User.Role.ADMIN]


@login_required
def item_list_view(request):
    item_type = request.GET.get("type", "")
    qs = Item.objects.all()

    if item_type in ["lost", "found"]:
        qs = qs.filter(item_type=item_type)

    # show only open-ish items to students (staff can see all from staff page)
    if not _is_staff(request.user):
        qs = qs.exclude(status=Item.Status.CLOSED)

    qs = qs.annotate(claim_count=Count("claims"))

    return render(request, "lostfound/item_list.html", {"items": qs, "type_filter": item_type})


@login_required
def item_detail_view(request, pk):
    item = get_object_or_404(Item, pk=pk)
    already_claimed = Claim.objects.filter(item=item, student=request.user).exists()

    return render(
        request,
        "lostfound/item_detail.html",
        {
            "item": item,
            "already_claimed": already_claimed,
            "claims": item.claims.select_related("student").all() if _is_staff(request.user) else None,
        },
    )


@login_required
def item_create_view(request):
    # students post lost/found items
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Item posted successfully ✅")
            return redirect("lostfound:detail", pk=obj.pk)
    else:
        form = ItemForm()

    return render(request, "lostfound/item_form.html", {"form": form})


@login_required
def claim_create_view(request, pk):
    item = get_object_or_404(Item, pk=pk)

    # Only students can claim
    if request.user.role != User.Role.STUDENT:
        messages.error(request, "Only students can submit claims.")
        return redirect("lostfound:detail", pk=item.pk)

    if item.status != Item.Status.OPEN:
        messages.error(request, "This item is not open for claims.")
        return redirect("lostfound:detail", pk=item.pk)

    if Claim.objects.filter(item=item, student=request.user).exists():
        messages.info(request, "You already submitted a claim for this item.")
        return redirect("lostfound:detail", pk=item.pk)

    if request.method == "POST":
        form = ClaimForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.item = item
            c.student = request.user
            c.save()
            messages.success(request, "Claim submitted! Staff will review it ✅")
            return redirect("lostfound:detail", pk=item.pk)
    else:
        form = ClaimForm(initial={"email": getattr(request.user, "email", "")})

    return render(request, "lostfound/claim_form.html", {"form": form, "item": item})


@login_required
def my_items_view(request):
    qs = Item.objects.filter(created_by=request.user)
    return render(request, "lostfound/my_items.html", {"items": qs})


@login_required
def my_claims_view(request):
    qs = Claim.objects.filter(student=request.user).select_related("item")
    return render(request, "lostfound/my_claims.html", {"claims": qs})


# ================== STAFF VIEWS ==================

@login_required
def staff_items_view(request):
    if not _is_staff(request.user):
        messages.error(request, "Not allowed.")
        return redirect("lostfound:list")

    qs = Item.objects.all().annotate(claim_count=Count("claims"))
    return render(request, "lostfound/staff_items.html", {"items": qs})


@login_required
def staff_claims_view(request):
    if not _is_staff(request.user):
        messages.error(request, "Not allowed.")
        return redirect("lostfound:list")

    qs = Claim.objects.select_related("item", "student").all()
    return render(request, "lostfound/staff_claims.html", {"claims": qs})


@login_required
def claim_approve_view(request, pk):
    if not _is_staff(request.user):
        messages.error(request, "Not allowed.")
        return redirect("lostfound:list")

    claim = get_object_or_404(Claim, pk=pk)
    claim.status = Claim.Status.APPROVED
    claim.reviewed_by = request.user
    claim.reviewed_at = timezone.now()
    claim.save()

    # mark item returned (simple behaviour)
    claim.item.status = Item.Status.RETURNED
    claim.item.save()

    messages.success(request, "Claim approved ✅ Item marked as Returned.")
    return redirect("lostfound:staff_claims")


@login_required
def claim_reject_view(request, pk):
    if not _is_staff(request.user):
        messages.error(request, "Not allowed.")
        return redirect("lostfound:list")

    claim = get_object_or_404(Claim, pk=pk)
    claim.status = Claim.Status.REJECTED
    claim.reviewed_by = request.user
    claim.reviewed_at = timezone.now()
    claim.save()

    messages.info(request, "Claim rejected.")
    return redirect("lostfound:staff_claims")


@login_required
def item_mark_returned_view(request, pk):
    if not _is_staff(request.user):
        messages.error(request, "Not allowed.")
        return redirect("lostfound:list")

    item = get_object_or_404(Item, pk=pk)
    item.status = Item.Status.RETURNED
    item.save()
    messages.success(request, "Item marked as Returned ✅")
    return redirect("lostfound:staff_items")

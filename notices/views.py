from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NoticeForm
from .models import Notice
from .permissions import can_manage_notices


@login_required
def notice_list_view(request):
    # Students see active only, Staff/Admin can optionally see archived (later)
    notices = Notice.objects.filter(is_active=True)

    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category", "").strip()

    if q:
        notices = notices.filter(title__icontains=q) | notices.filter(content__icontains=q)

    if cat:
        notices = notices.filter(category=cat)

    return render(
        request,
        "notices/notice_list.html",
        {
            "notices": notices,
            "q": q,
            "cat": cat,
            "can_manage": can_manage_notices(request.user),
        },
    )


@login_required
def notice_detail_view(request, pk):
    notice = get_object_or_404(Notice, pk=pk, is_active=True)
    return render(
        request,
        "notices/notice_detail.html",
        {"notice": notice, "can_manage": can_manage_notices(request.user)},
    )


@login_required
def notice_create_view(request):
    if not can_manage_notices(request.user):
        messages.error(request, "You do not have permission to create notices.")
        return redirect("notices:list")

    if request.method == "POST":
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            messages.success(request, "Notice published successfully.")
            return redirect("notices:detail", pk=notice.pk)
    else:
        form = NoticeForm()

    return render(request, "notices/notice_form.html", {"form": form, "mode": "create"})


@login_required
def notice_edit_view(request, pk):
    if not can_manage_notices(request.user):
        messages.error(request, "You do not have permission to edit notices.")
        return redirect("notices:list")

    notice = get_object_or_404(Notice, pk=pk)
    if not notice.is_active:
        raise Http404("Notice not found.")

    if request.method == "POST":
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            messages.success(request, "Notice updated successfully.")
            return redirect("notices:detail", pk=notice.pk)
    else:
        form = NoticeForm(instance=notice)

    return render(request, "notices/notice_form.html", {"form": form, "mode": "edit", "notice": notice})


@login_required
def notice_archive_view(request, pk):
    if not can_manage_notices(request.user):
        messages.error(request, "You do not have permission to archive notices.")
        return redirect("notices:list")

    notice = get_object_or_404(Notice, pk=pk)

    if request.method == "POST":
        notice.is_active = False
        notice.save(update_fields=["is_active"])
        messages.success(request, "Notice archived.")
        return redirect("notices:list")

    return render(request, "notices/notice_archive_confirm.html", {"notice": notice})

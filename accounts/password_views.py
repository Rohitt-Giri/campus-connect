# accounts/password_views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect

@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        for f in form.fields.values():
            f.widget.attrs.update({"class": "form-control"})
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully ✅")
            return redirect("accounts:my_profile")
        messages.error(request, "Please fix the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)
        for f in form.fields.values():
            f.widget.attrs.update({"class": "form-control"})

    return render(request, "accounts/change_password.html", {"form": form})
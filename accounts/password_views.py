# accounts/password_views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect

from .email_utils import send_password_changed_email

@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        for f in form.fields.values():
            f.widget.attrs.update({"class": "form-control"})
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            try:
                print(f"[EMAIL DEBUG] Sending password change email to {request.user.email}")
                sent = send_password_changed_email(request.user)
                print(f"[EMAIL DEBUG] Result: {sent}")
            except Exception as e:
                print(f"[EMAIL ERROR] Password change email failed: {e}")

            messages.success(request, "Password changed successfully ✅")
            return redirect("accounts:my_profile")
        messages.error(request, "Please fix the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)
        for f in form.fields.values():
            f.widget.attrs.update({"class": "form-control"})

    return render(request, "accounts/change_password.html", {"form": form})
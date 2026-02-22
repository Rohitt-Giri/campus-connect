# accounts/password_views.py
from django.contrib.auth.views import PasswordResetConfirmView
from django.urls import reverse_lazy
from django.contrib import messages

from accounts.email_utils import send_password_changed_email


class CampusPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Overrides Django reset-confirm to send a security email after password is changed.
    """
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")

    def form_valid(self, form):
        response = super().form_valid(form)

        # After password is changed successfully, self.user is available
        user = getattr(self, "user", None)
        if user:
            sent = send_password_changed_email(user)
            if sent:
                messages.success(self.request, "Password updated ✅ (Email sent)")
            else:
                messages.success(self.request, "Password updated ✅")
        else:
            messages.success(self.request, "Password updated ✅")

        return response
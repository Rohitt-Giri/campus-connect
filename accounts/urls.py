from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from accounts import admin_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("pending/", views.pending_approval_view, name="pending"),
    path("go/", views.post_login_redirect_view, name="post_login_redirect"),

    # ✅ Profile (use views.my_profile_view)
    path("me/", views.my_profile_view, name="my_profile"),

    # ✅ Change password (button inside profile)
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/change_password.html",
            success_url=reverse_lazy("accounts:my_profile"),
        ),
        name="change_password",
    ),

    # Admin dashboard
    path("admin-dashboard/", admin_views.admin_dashboard_view, name="admin_dashboard"),
    path("admin/approve/<int:user_id>/", admin_views.approve_user_view, name="admin_approve_user"),
    path("admin/reject/<int:user_id>/", admin_views.reject_user_view, name="admin_reject_user"),
    path("admin/change-role/<int:user_id>/", admin_views.change_role_view, name="admin_change_role"),
    path("admin/users/", admin_views.admin_users_view, name="admin_users"),
    path("admin/toggle-active/<int:user_id>/", admin_views.toggle_active_view, name="admin_toggle_active"),
    path(
        "admin/users/<int:user_id>/resend-approval-email/",
        admin_views.resend_approval_email_view,
        name="admin_resend_approval_email"
    ),

    # Password reset (PRO UI)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            html_email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
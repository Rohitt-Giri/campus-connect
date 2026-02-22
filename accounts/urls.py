from django.urls import path

from accounts import admin_views
from . import views
from django.contrib.auth import views as auth_views
from accounts.password_views import CampusPasswordResetConfirmView

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("pending/", views.pending_approval_view, name="pending"),

    # Custom admin dashboard
    path("admin-dashboard/", admin_views.admin_dashboard_view, name="admin_dashboard"),
    path("admin/approve/<int:user_id>/", admin_views.approve_user_view, name="admin_approve_user"),
    path("admin/reject/<int:user_id>/", admin_views.reject_user_view, name="admin_reject_user"),
    path("admin/change-role/<int:user_id>/", admin_views.change_role_view, name="admin_change_role"),

    # Admin user management
    path("admin/users/", admin_views.admin_users_view, name="admin_users"),
    path("admin/toggle-active/<int:user_id>/", admin_views.toggle_active_view, name="admin_toggle_active"),

    # ✅ resend approval email (FIXED)
    path(
        "admin/users/<int:user_id>/resend-approval-email/",
        admin_views.resend_approval_email_view,
        name="admin_resend_approval_email"
    ),

    # Password reset
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset_form.html",
        email_template_name="registration/password_reset_email.txt",
        html_email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt",
        success_url="/accounts/password-reset/done/",
    ), name="password_reset"),

    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_done.html",
    ), name="password_reset_done"),

    path("reset/<uidb64>/<token>/", CampusPasswordResetConfirmView.as_view(
        # template already set in class, but ok either way
    ), name="password_reset_confirm"),

    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_complete.html",
    ), name="password_reset_complete"),
]
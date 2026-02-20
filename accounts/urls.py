from django.urls import path

from accounts import admin_views
from . import views

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
]

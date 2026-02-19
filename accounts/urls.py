from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("pending/", views.pending_approval_view, name="pending"),

    # Custom admin dashboard
    path("admin-dashboard/", views.admin_dashboard_view, name="admin_dashboard"),
    path("admin-dashboard/approve/<int:user_id>/", views.approve_user_view, name="admin_approve_user"),
    path("admin-dashboard/reject/<int:user_id>/", views.reject_user_view, name="admin_reject_user"),
]

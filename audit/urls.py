from django.urls import path
from . import views

app_name = "audit"

urlpatterns = [
    path("", views.admin_audit_logs_view, name="admin_logs"),
]
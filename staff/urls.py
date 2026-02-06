from django.urls import path
from . import views

app_name = "staff"

urlpatterns = [
    path("dashboard/", views.staff_dashboard_view, name="dashboard"),
]

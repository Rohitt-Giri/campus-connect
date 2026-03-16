from django.urls import path
from . import views

app_name = "student"

urlpatterns = [
    path("dashboard/", views.student_dashboard_view, name="dashboard"),
    path("my-registrations/", views.my_registrations_view, name="my_registrations"),
]

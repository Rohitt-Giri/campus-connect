from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.events_list_view, name="list"),
    path("create/", views.event_create_view, name="create"),
    path("<int:pk>/", views.event_detail_view, name="detail"),
    path("<int:pk>/register/", views.event_register_view, name="register"),
    path("<int:pk>/registrations/", views.event_registrations_view, name="registrations"),
]

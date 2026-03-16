from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.events_list_view, name="list"),
    path("create/", views.event_create_view, name="create"),
    path("<int:pk>/", views.event_detail_view, name="detail"),
    path("<int:pk>/register/", views.event_register_view, name="register"),
    path("<int:pk>/registrations/", views.event_registrations_view, name="registrations"),
    path("<int:pk>/registrations/export/", views.event_registrations_export_csv_view, name="registrations_export"),

    # ✅ Edit + Archive (like notices)
    path("<int:pk>/edit/", views.event_edit_view, name="edit"),
    path("<int:pk>/archive/", views.event_archive_confirm_view, name="archive_confirm"),
    path("<int:pk>/archive/confirm/", views.event_archive_view, name="archive"),
    
]

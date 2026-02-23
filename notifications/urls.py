# notifications/urls.py
from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notifications_list_view, name="list"),
    path("go/<int:pk>/", views.notification_go_view, name="go"),
    path("read/<int:pk>/", views.notifications_mark_read_view, name="mark_read"),
    path("read-all/", views.notifications_mark_all_read_view, name="mark_all_read"),
]
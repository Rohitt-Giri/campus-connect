from django.urls import path
from . import views

app_name = "notices"

urlpatterns = [
    path("", views.notice_list_view, name="list"),
    path("create/", views.notice_create_view, name="create"),
    path("<int:pk>/", views.notice_detail_view, name="detail"),
    path("<int:pk>/edit/", views.notice_edit_view, name="edit"),
    path("<int:pk>/archive/", views.notice_archive_view, name="archive"),
]

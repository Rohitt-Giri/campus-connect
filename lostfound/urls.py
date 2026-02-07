from django.urls import path
from . import views

app_name = "lostfound"

urlpatterns = [
    # Student
    path("", views.item_list_view, name="list"),
    path("create/", views.item_create_view, name="create"),
    path("<int:pk>/", views.item_detail_view, name="detail"),
    path("<int:pk>/claim/", views.claim_create_view, name="claim"),
    path("my-items/", views.my_items_view, name="my_items"),
    path("my-claims/", views.my_claims_view, name="my_claims"),

    # Staff
    path("staff/items/", views.staff_items_view, name="staff_items"),
    path("staff/claims/", views.staff_claims_view, name="staff_claims"),
    path("staff/claims/<int:pk>/approve/", views.claim_approve_view, name="claim_approve"),
    path("staff/claims/<int:pk>/reject/", views.claim_reject_view, name="claim_reject"),
    path("staff/items/<int:pk>/mark-returned/", views.item_mark_returned_view, name="mark_returned"),
]

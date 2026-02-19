from django.urls import path
from . import views

app_name = "lostfound"

urlpatterns = [
    # Student
    path("", views.items_list_view, name="list"),
    path("create/", views.item_create_view, name="create"),
    path("<int:pk>/", views.item_detail_view, name="detail"),
    path("<int:pk>/claim/", views.claim_create_view, name="claim"),
    path("my-posts/", views.my_posts_view, name="my_posts"),
    path("my-claims/", views.my_claims_view, name="my_claims"),

    # Staff
    path("staff/items/", views.staff_items_view, name="staff_items"),
    path("staff/items/<int:pk>/mark-returned/", views.staff_mark_returned_view, name="staff_mark_returned"),
    path("staff/claims/", views.staff_claims_view, name="staff_claims"),
    path("staff/claims/<int:pk>/review/", views.staff_claim_review_view, name="staff_claim_review"),
]

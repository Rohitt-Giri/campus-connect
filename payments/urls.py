from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("submit/<int:registration_id>/", views.payment_submit_view, name="submit"),
    path("staff/", views.staff_payments_list_view, name="staff_list"),
    path("staff/review/<int:proof_id>/", views.staff_payment_review_view, name="staff_review"),
    path("staff/<int:proof_id>/action/", views.staff_payment_action_view, name="staff_action"),
]

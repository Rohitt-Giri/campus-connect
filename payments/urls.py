from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    # Student
    path("my/", views.student_payments_list_view, name="my_payments"),
    path("submit/<int:registration_id>/", views.payment_submit_view, name="submit"),

    # eSewa callbacks
    path("esewa/success/", views.esewa_success_view, name="esewa_success"),
    path("esewa/failure/<int:registration_id>/", views.esewa_failure_view, name="esewa_failure"),

    # Staff
    path("staff/", views.staff_payments_list_view, name="staff_list"),
    path("staff/review/<int:proof_id>/", views.staff_payment_review_view, name="staff_review"),
    path("staff/<int:proof_id>/action/", views.staff_payment_action_view, name="staff_action"),
]

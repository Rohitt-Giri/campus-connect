from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("submit/<int:registration_id>/", views.payment_submit_view, name="submit"),

    # staff/admin
    path("staff/", views.staff_payments_list_view, name="staff_list"),
    path("staff/<int:pk>/<str:action>/", views.staff_payment_decide_view, name="staff_decide"),
]

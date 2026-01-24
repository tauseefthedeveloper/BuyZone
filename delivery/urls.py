from django.urls import path
from . import views

urlpatterns = [
     path("dashboard/", views.delivery_dashboard, name="delivery_dashboard"),
    path("start/<int:order_id>/", views.generate_delivery_otp, name="generate_delivery_otp"),
    path("verify/<int:order_id>/", views.verify_delivery_otp, name="verify_delivery_otp"),
    path("stats/", views.delivery_stats, name="delivery_stats"),
    path("return/", views.return_order_picked, name="return_dashboard"),
    path("mark_return_picked/<int:order_id>/", views.mark_return_picked, name="mark_return_picked"),
    path("orderDetails/<str:order_id>", views.orderDetails, name="orderDetails"),

]

from django.urls import path
from buyzoneapp import views

urlpatterns = [
    path('',views.index,name="index"),
    path('contact/',views.contact,name="contact"),
    path('about/',views.about,name="about"),
    path('profile/',views.profile,name="profile"),
    path('sign/',views.sign,name="sign"),
    path('checkout/',views.checkout,name="checkout"),
    path('handlerequest/',views.handlerequest,name="HandleRequest"),
    path('paymentstatus/', views.payment_status, name='payment_status'),
    path('productDetails/<int:product_id>/', views.productDetails, name='productDetails'),
    path('category/<str:category>/', views.category_products, name='category_products'),
    path('cancel_order/<str:order_id>/', views.cancel_order, name='cancel_order'),
    path('return_order/<str:order_id>/', views.return_order, name='return_order'),
    path('order_activity/<str:order_id>/', views.order_activity, name='order_activity'),
    path("search/", views.search, name="search"),
]
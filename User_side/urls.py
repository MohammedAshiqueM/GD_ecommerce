from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.userLogin,name='userLogin'),
    path('home',views.userHome,name='userHome'),
    path('otp/', views.otp, name='otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('productDetails/<pk>', views.productDetails, name='productDetails'),
    path('shop/', views.shop, name='shop'),
    path('checkout/', views.checkOut, name='checkOut'),
    path('cart/', views.cart, name='cart'),
    path('contact/', views.contact, name='contacty'),
    
    
    
]
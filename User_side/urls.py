from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.userLogin,name='userLogin'),
    path('home',views.userHome,name='userHome'),
    path('otp/', views.otp, name='otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('productDetails/<pk>', views.productDetails, name='productDetails'),
    path('shop/', views.shop, name='shop'),
    path('categoryProduct/<pk>', views.categoryProduct, name='categoryProduct'),
    path('subcategoryProduct/<pk>', views.subcategoryProduct, name='subcategoryProduct'),
    path('checkout/', views.checkOut, name='checkout'),
    path('cart/', views.cart, name='cart'),
    path('contact/', views.contact, name='contact'),
    path('logout/', views.logout, name='logout'),
    path('get-product-combination/<int:product_id>/', views.get_product_combination, name='get_product_combination'),
    
    
    
]
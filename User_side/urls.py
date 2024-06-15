from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.userLogin,name='userLogin'),
    path('home',views.userHome,name='userHome'),
    path('otp/', views.otp, name='otp'),
 path('resend-otp/', views.resend_otp, name='resend_otp'),
    
]
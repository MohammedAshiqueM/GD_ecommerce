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
    path('profile/<pk>', views.profile, name='profile'),
    path('editProfile/<pk>', views.editProfile, name='editProfile'),
    path('addAddress/<pk>', views.addAddress, name='addAddress'),
    path('set_default_address/', views.set_default_address, name='set_default_address'),
    path('editAddress/<pk>', views.editAddress, name='editAddress'),
    path('deleteAddress/<pk>', views.deleteAddress, name='deleteAddress'),
    
    path('cart/', views.cart_view, name='cart'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'), 
    path('get_configuration_id/', views.get_configuration_id, name='get_configuration_id'),
    path('increment-quantity/<int:item_id>/', views.increment_quantity, name='increment_quantity'),
    path('decrement-quantity/<int:item_id>/', views.decrement_quantity, name='decrement_quantity'),
    path('remove-cart-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.checkOut, name='checkout'),
    
    # path('cart/', views.cart, name='cart'),
    path('contact/', views.contact, name='contact'),
    path('logout/', views.logout, name='logout'),
    # path('get_product_combination/<int:product_id>/', views.get_product_combination, name='get_product_combination'),
    
    
    path('get_configuration_id/', views.get_configuration_id, name='get_configuration_id'),
    path('check_cart_quantity/', views.check_cart_quantity, name='check_cart_quantity'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('place_order/', views.place_order, name='place_order'),
    path('order_success/', views.order_success, name='order_success'),
    
    path('my_orders/', views.my_orders, name='my_orders'),
    path('user/cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    
]
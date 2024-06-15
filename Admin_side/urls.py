from django.urls import path
from . import views

urlpatterns = [
    path('', views.adminLogin, name="adminLogin"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('customers/', views.customers, name='customers'),
    path('block/<int:pk>/', views.block, name='block'),
    path('unblock/<int:pk>/', views.unblock, name='unblock'),
    path('category/', views.category, name='category'),
    path('addCategory/', views.addCategory, name='addCategory'),
    path('editCategory/<pk>/', views.editCategory, name='editCategory'),
    path('editSubcategory/<pk>/', views.editSubcategory, name='editSubcategory'),
    path('blockCategory/<int:pk>/', views.blockCategory, name='blockCategory'),
    path('unblockCategory/<int:pk>/', views.unblockCategory, name='unblockCategory'),
    path('blockSubcategory/<int:pk>/', views.blockSubcategory, name='blockSubcategory'),
    path('unblockSubcategory/<int:pk>/', views.unblockSubcategory, name='unblockSubcategory'),
    path('product/', views.product, name='product'),
    path('addProduct/', views.addProduct, name='addProduct'),
    path('blockProduct/<int:pk>/', views.blockProduct, name='blockProduct'),
    path('unblockProduct/<int:pk>/', views.unblockProduct, name='unblockProduct'),
    path('get_subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),
    path('editProduct/<pk>/', views.editProduct, name='editProduct'),
    
]

from django.contrib import admin

# Register your models here.
from .models import (
    User,
    Address,
    PaymentType,
    PaymentMethod,
    Category,
    SubCategory,
    Variation,
    VariationOption,
    Product,
    ProductConfiguration,
    Cart,
    CartItem,
    ShippingMethod,
    OrderStatus,
    Order,
    OrderLine,
    Review,
    Promotion,
    PromotionCategory,
    ProductImage,
)

admin.site.register(
    [
        Address,
        PaymentType,
        PaymentMethod,
        Category,
        SubCategory,
        Variation,
        VariationOption,
        Product,
        ProductConfiguration,
        Cart,
        CartItem,
        ShippingMethod,
        OrderStatus,
        Order,
        OrderLine,
        Review,
        Promotion,
        PromotionCategory,
        ProductImage,
    ]
)

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    unit_number = models.CharField(max_length=10, blank=True, null=True)
    street_number = models.CharField(max_length=10)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255)
    region = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)

class PaymentType(models.Model):
    value = models.CharField(max_length=255)

class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)
    expiry_date = models.DateField()
    is_default = models.BooleanField(default=False)

class Category(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    # reminder ! add image
    def __str__(self):
        return f"{self.name}"

class SubCategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    # reminder ! add image
    def __str__(self):
        return f"{self.name}"

class Variation(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class VariationOption(models.Model):
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='products',null=True, blank=True) 
    SKU = models.CharField(max_length=255, unique=True)
    qty_in_stock = models.IntegerField()
    price = models.FloatField()
    product_image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')


class ProductConfiguration(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_option = models.ForeignKey(VariationOption, on_delete=models.CASCADE)

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField()

class ShippingMethod(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()

class OrderStatus(models.Model):
    status = models.CharField(max_length=255)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(Address, on_delete=models.CASCADE)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE)
    order_total = models.FloatField()
    order_status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)

class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.IntegerField()
    price = models.FloatField()

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered_product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating_value = models.IntegerField()
    comment = models.TextField()

class Promotion(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    discount_rate = models.FloatField()
    start_date = models.DateField()
    end_date = models.DateField()

class PromotionCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='promotion_categories')
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE)

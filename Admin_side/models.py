from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import django.utils.timezone as timezone

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
    def __str__(self):
        return f"{self.value}"
    
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
    category_image = models.ImageField(upload_to='category/', blank=True, null=True)
    def __str__(self):
        return f"{self.name}"

class SubCategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    # reminder ! add image
    def __str__(self):
        return f"{self.name}"

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='products',null=True, blank=True) 
    SKU = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)  # Add this field if needed
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    
    def has_combination_with_variation(self, variation_id):
        return self.configurations.filter(variation_options__variation_id=variation_id).exists()

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class VariationOption(models.Model):
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product/')


class ProductConfiguration(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='configurations')
    variation_options = models.ManyToManyField(VariationOption, related_name='configurations')
    price = models.FloatField(default=0.0)
    qty_in_stock = models.IntegerField(default=0)

    def __str__(self):
        options_str = ', '.join(option.value for option in self.variation_options.all())
        return f"{self.product.name} - {options_str}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_configuration = models.ForeignKey(ProductConfiguration, on_delete=models.CASCADE, null=True, blank=True) 
    qty = models.PositiveIntegerField(default=1) 

class ShippingMethod(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=[('percentage', 'Percentage'), ('fixed', 'Fixed')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # New field for minimum purchase amount
    image = models.ImageField(upload_to='coupons/', null=True, blank=True)  # Image for coupon card
    details = models.TextField(null=True)
    
    def __str__(self):
        return self.code
    
    def clean(self):
        if self.discount_value < 0:
            raise ValidationError('Discount value cannot be negative.')
        if self.min_purchase_amount < 0:
            raise ValidationError('Minimum purchase amount cannot be negative.')
        if self.usage_limit <= 0:
            raise ValidationError('Usage limit must be greater than 0.')
        
    def is_valid(self, order_total):
        now = timezone.now()
        return (
            self.active and
            self.valid_from <= now <= self.valid_to and
            order_total >= self.min_purchase_amount
        )
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
       
class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    usage_date = models.DateTimeField(auto_now_add=True)
     
class OrderStatus(models.Model):
    status = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.status}"
    
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(Address, on_delete=models.CASCADE)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE,null=True)
    order_total = models.FloatField()
    order_status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def calculate_total(self):
        total = sum(item.get_total_price() for item in self.orderline_set.all())
        if self.coupon and self.coupon.is_valid(total):
            if self.coupon.discount_type == 'percentage':
                discount = total * (self.coupon.discount_value / 100)
            else:
                discount = self.coupon.discount_value
            self.discount_amount = min(discount, total)  # Ensure discount does not exceed total
            total -= self.discount_amount
        else:
            self.discount_amount = 0
        self.order_total = total
        self.save()
        return total
    
    
class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_configuration = models.ForeignKey(ProductConfiguration, on_delete=models.CASCADE, null=True, blank=True)
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


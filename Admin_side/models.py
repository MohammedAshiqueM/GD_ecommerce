from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import django.utils.timezone as timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


#Address model
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

#Payment type model(Pending,Completed,Failed)
class PaymentType(models.Model):
    value = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.value}"
    
#Payment method for each orders
class PaymentMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)
    expiry_date = models.DateField()
    is_default = models.BooleanField(default=False)

#Category schema
class Category(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    category_image = models.ImageField(upload_to='category/', blank=True, null=True)
    def __str__(self):
        return f"{self.name}"

#Subcategory schema with category foreign key
class SubCategory(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    # reminder ! add image
    def __str__(self):
        return f"{self.name}"

#Product model with category and subcategory as foreign key
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='products',null=True, blank=True) 
    SKU = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)  # Add this field if needed
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    
    def __str__(self):
        return f"{self.name}"
    
    def has_combination_with_variation(self, variation_id):
        return self.configurations.filter(variation_options__variation_id=variation_id).exists()
    
#Offer model with type percentage and fixed
class Offer(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    discount_type = models.CharField(max_length=20, choices=[
        ('PERCENTAGE', 'Percentage'),
        ('FIXED', 'Fixed Amount'),
    ])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

#Variation model for adding variations for product
class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

#Variation option model with foreign key variation,for adding options in variations
class VariationOption(models.Model):
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

#Product images model with product foreign key  
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product/')

#Product configuration schema for adding stock and price seperately to each product vaiants
class ProductConfiguration(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='configurations')
    variation_options = models.ManyToManyField(VariationOption, related_name='configurations')
    price = models.FloatField(default=0.0)
    qty_in_stock = models.IntegerField(default=0)

    def __str__(self):
        options_str = ', '.join(option.value for option in self.variation_options.all())
        return f"{self.product.name} - {options_str}"

    def get_applicable_offers(self):
        now = timezone.now()
        product_offers = self.offers.filter(
            offer__is_active=True,
            offer__start_date__lte=now,
            offer__end_date__gte=now,
            offer__min_product_price__lte=self.price
        )
        category_offers = self.product.category.offers.filter(
            offer__is_active=True,
            offer__start_date__lte=now,
            offer__end_date__gte=now,
            offer__min_product_price__lte=self.price
        )
        subcategory_offers = self.product.subcategory.offers.filter(
            offer__is_active=True,
            offer__start_date__lte=now,
            offer__end_date__gte=now,
            offer__min_product_price__lte=self.price
        )

        all_offers = list(product_offers) + list(category_offers) + list(subcategory_offers)
        return sorted(all_offers, key=lambda x: (x.offer.discount_type == 'PERCENTAGE', x.offer.discount_value), reverse=True)

    def get_discounted_price(self):
        applicable_offers = self.get_applicable_offers()
        
        if not applicable_offers:
            return Decimal(self.price)

        best_offer = applicable_offers[0]
        if best_offer.offer.discount_type == 'FIXED':
            discount = best_offer.offer.discount_value
        else:  # Percentage
            discount = Decimal(self.price) * (best_offer.offer.discount_value / 100)

        return max(Decimal(self.price) - Decimal(discount), Decimal('0.00'))

#For adding product offers 
class ProductOffer(models.Model):
    proproduct_configuration = models.ForeignKey(ProductConfiguration, on_delete=models.CASCADE, related_name='offers',null=True)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)

    # class Meta:
    #     unique_together = ('product_configuration', 'offer')
    
    # def has_combination_with_variation(self, variation_id):
    #     return self.configurations.filter(variation_options__variation_id=variation_id).exists()
    
#User Cart model
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

#Cart item with cart and product configuration as foreign key
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_configuration = models.ForeignKey(ProductConfiguration, on_delete=models.CASCADE, null=True, blank=True) 
    qty = models.PositiveIntegerField(default=1) 

#Shipping methods (For later usage)
class ShippingMethod(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()

#Coupon model
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
        
    def is_valid(self, order_total, user):
        now = timezone.now()
        user_usage_count = self.couponusage_set.filter(user=user).count()
        # total_usage_count = self.couponusage_set.count()

        return (
            self.active and
            self.valid_from <= now <= self.valid_to and
            order_total >= self.min_purchase_amount and
            user_usage_count < self.usage_limit 
            
        )

    def available_for_user(self, user):
        user_usage_count = self.couponusage_set.filter(user=user).count()
        total_usage_count = self.couponusage_set.count()
        return user_usage_count < self.usage_limit and total_usage_count < self.usage_limit

#To count the coupon usage by a user    
class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    usage_date = models.DateTimeField(auto_now_add=True)
     
#Order status (Pending,Completed,Canelled)
class OrderStatus(models.Model):
    status = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.status}"

#Peyment status model(Payment Pending,Payment Refunded,Payment Completed)  
class PaymentStatus(models.Model):
    status = models.CharField(max_length=255)

    def __str__(self):
        return self.status
    
#Order model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(Address, on_delete=models.CASCADE)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE,null=True)
    order_total = models.FloatField()
    order_status = models.ForeignKey(OrderStatus, on_delete=models.CASCADE)
    payment_status = models.ForeignKey(PaymentStatus, on_delete=models.CASCADE,null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    permanent_address_line1 = models.CharField(max_length=255, null=True)
    permanent_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    permanent_city = models.CharField(max_length=100, null=True)
    permanent_state = models.CharField(max_length=100, null=True)
    permanent_country = models.CharField(max_length=100, null=True)
    permanent_postal_code = models.CharField(max_length=20, null=True)
    
    def calculate_total(self):
        total = sum(Decimal(item.get_total_price()) for item in self.orderline_set.all())
        if self.coupon and self.coupon.is_valid(total):
            if self.coupon.discount_type == 'percentage':
                discount = total * (Decimal(self.coupon.discount_value) / Decimal(100))
            else:
                discount = Decimal(self.coupon.discount_value)
            self.discount_amount = min(discount, total)  # Ensure discount does not exceed total
            total -= self.discount_amount
        else:
            self.discount_amount = Decimal('0.00')
        self.order_total = total
        self.save()
        return total

    
    def cancel_and_refund(self):
        if self.order_status.status != 'Cancelled':  # Assuming you have an OrderStatus model
            wallet, _ = Wallet.objects.get_or_create(user=self.user)
            refund_amount = self.order_total  # Or calculate based on your business logic
            wallet.add_funds(refund_amount)
            
            Transaction.objects.create(
                wallet=wallet,
                amount=refund_amount,
                transaction_type='Refund',
                order=self
            )

            self.order_status = OrderStatus.objects.get(status='Cancelled')
            self.save()

            return True
        return False
    
    def get_return_status(self):
        return_request = self.orderreturn_set.first()
        if return_request:
            return return_request.return_status.status
        return None
    
#Order line with order as foreign key,which contains the product, price and quantites of the orders are saving in this schema
class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_configuration = models.ForeignKey(ProductConfiguration, on_delete=models.CASCADE, null=True, blank=True)
    qty = models.IntegerField()
    price = models.FloatField()
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2,null=True)

#Reviews(for later updation)
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered_product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating_value = models.IntegerField()
    comment = models.TextField()

#For adding discounts
class Promotion(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    discount_rate = models.FloatField()
    start_date = models.DateField()
    end_date = models.DateField()

#For mention the category for discount
class PromotionCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='promotion_categories')
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE)

#Wishlist of the user
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
#Wishlist Item model for storing items of the wishlist
class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product_configuration = models.ForeignKey(ProductConfiguration, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('wishlist', 'product_configuration')

#Wallet of the user
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet"
    
    def add_funds(self, amount):
        self.balance += Decimal(amount)
        self.save()

    def deduct_funds(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False    

#Transaction types of the user 
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('ADD', 'Add Funds'),
        ('WITHDRAW', 'Withdraw Funds'),#this fields are created for later updation with ADD and WITHDRAW funds later
        ('PURCHASE', 'Purchase'),
        ('REFUND', 'Refund'),
    )
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - {self.amount}"
    
#Categroy offer model
class CategoryOffer(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='offers')
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('category', 'offer')

#Sub categroy offer model
class SubcategoryOffer(models.Model):
    subcategory = models.ForeignKey('Subcategory', on_delete=models.CASCADE, related_name='offers')
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('subcategory', 'offer')
#Sales report of admin        
class SalesReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)
    total_orders = models.IntegerField()
    total_discount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sales Report {self.start_date} to {self.end_date}"

#Bannere model for adding banner by user
class CarouselBanner(models.Model):
    POSITIONS = (
        (1, 'First'),
        (2, 'Second'),
        (3, 'Third'),
    )

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='banners/carousel/')
    position = models.IntegerField(choices=POSITIONS, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Carousel Banner - Position {self.position}"

    class Meta:
        ordering = ['position']

#Offer banner model
class OfferBanner(models.Model):
    POSITIONS = (
        (1, 'Top'),
        (2, 'Bottom'),
    )

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True, null=True)
    image = models.ImageField(upload_to='banners/offer/')
    position = models.IntegerField(choices=POSITIONS, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Offer Banner - {self.get_position_display()}"

    class Meta:
        ordering = ['position']

    def clean(self):
        if OfferBanner.objects.exclude(pk=self.pk).count() >= 2:
            raise ValidationError("You can only have two Offer Banners.")

#Options for admin to return orders       
class OrderReturnStatus(models.Model):
    status = models.CharField(max_length=255, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ])

    def __str__(self):
        return self.status

#Modal for return orders       
class OrderReturn(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    return_reason = models.TextField()
    return_status = models.ForeignKey(OrderReturnStatus, on_delete=models.CASCADE)
    admin_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return for Order {self.order.id} - Status: {self.return_status}"

#Permanent address for storing while placing the order, hence the address of the user never changes the address on changing the address in the profile 
class PermanentAddress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='permanent_address')
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.username}'s Permanent Address"
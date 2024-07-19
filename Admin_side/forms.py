from django import forms
from .models import Coupon,Offer,Category,SubCategory,Product,ProductConfiguration,CarouselBanner,OfferBanner

# from django import forms
# from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'discount_type', 'valid_from', 'valid_to', 'discount_value', 
            'active', 'min_purchase_amount', 'usage_limit', 'image', 'details'
        ]
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_discount_value(self):
        discount_value = self.cleaned_data.get('discount_value')
        discount_type = self.cleaned_data.get('discount_type')
        min_purchase_amount = self.cleaned_data.get('min_purchase_amount')
        
        if discount_value is None:
            raise forms.ValidationError('Discount value is required.')
        
        if discount_type is None:
            raise forms.ValidationError('Discount type is required.')
        
        if min_purchase_amount is None:
            raise forms.ValidationError('Minimum purchase amount is required.')

        if discount_type == 'percentage':
            if not (0 < discount_value <= 100):
                raise forms.ValidationError('For percentage discounts, the value must be between 0 and 100.')
        elif discount_type == 'fixed':
            if discount_value <= 0:
                raise forms.ValidationError('Discount value must be a positive value.')
            if discount_value > min_purchase_amount:
                raise forms.ValidationError('Fixed discount value must not exceed the minimum purchase amount.')
        
        return discount_value

    def clean_valid_to(self):
        valid_from = self.cleaned_data.get('valid_from')
        valid_to = self.cleaned_data.get('valid_to')
        if valid_to <= valid_from:
            raise forms.ValidationError('Valid to date must be after valid from date.')
        return valid_to

    def clean_min_purchase_amount(self):
        min_purchase_amount = self.cleaned_data.get('min_purchase_amount')
        if min_purchase_amount < 0:
            raise forms.ValidationError('Minimum purchase amount cannot be negative.')
        return min_purchase_amount

    def clean_usage_limit(self):
        usage_limit = self.cleaned_data.get('usage_limit')
        if usage_limit <= 0:
            raise forms.ValidationError('Usage limit per user must be greater than 0.')
        return usage_limit
  
    
class OfferForm(forms.ModelForm):
    apply_to = forms.ChoiceField(choices=[('category', 'Category'), ('subcategory', 'Subcategory'), ('product', 'Product')], widget=forms.RadioSelect)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    subcategory = forms.ModelChoiceField(queryset=SubCategory.objects.all(), required=False)
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=False)
    product_configuration = forms.ModelChoiceField(queryset=ProductConfiguration.objects.all(), required=False)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product_configuration'].choices = [
            (config.id, f"{config.product.name} - {', '.join([f'{vo.variation.name}: {vo.value}' for vo in config.variation_options.all()])} - Price: {config.price}")
            for config in ProductConfiguration.objects.select_related('product').prefetch_related('variation_options__variation').all()
        ]

    class Meta:
        model = Offer
        fields = ['name', 'description', 'discount_type', 'discount_value', 'min_product_price', 'start_date', 'end_date', 'is_active', 'apply_to', 'product_configuration']   
    # ['name', 'description', 'discount_type', 'discount_value', 'min_product_price', 'start_date', 'end_date', 'is_active', 'apply_to']
    
class CarouselBannerForm(forms.ModelForm):
    class Meta:
        model = CarouselBanner
        fields = ['title', 'subtitle', 'image', 'position', 'is_active']

class OfferBannerForm(forms.ModelForm):
    class Meta:
        model = OfferBanner
        fields = ['title', 'subtitle', 'image', 'position','is_active']

    def clean(self):
        cleaned_data = super().clean()
        if OfferBanner.objects.exclude(pk=self.instance.pk).count() >= 2:
            raise forms.ValidationError("You can only have two Offer Banners.")
        return cleaned_data
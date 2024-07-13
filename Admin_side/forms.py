from django import forms
from .models import Coupon,Offer,Category,SubCategory,Product,ProductConfiguration

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code','discount_type', 'valid_from', 'valid_to', 'discount_value', 'active', 'min_purchase_amount','usage_limit','image','details']

        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        
    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount <= 0:
            raise forms.ValidationError('Discount must be a positive value.')
        return discount

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
    
    def usage_limit(self):
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
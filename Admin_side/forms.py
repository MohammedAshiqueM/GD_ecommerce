from django import forms
from .models import Coupon,Offer,Category,SubCategory,Product

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
    APPLY_CHOICES = [
        ('category', 'Category'),
        ('subcategory', 'Subcategory'),
        ('product', 'Product'),
    ]
    apply_to = forms.ChoiceField(choices=APPLY_CHOICES, widget=forms.RadioSelect)
    
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    subcategory = forms.ModelChoiceField(queryset=SubCategory.objects.all(), required=False)
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=False)

    class Meta:
        model = Offer
        fields = ['name', 'description', 'discount_type', 'discount_value', 'min_product_price', 'start_date', 'end_date', 'is_active', 'apply_to']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        apply_to = cleaned_data.get('apply_to')
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')
        product = cleaned_data.get('product')

        if apply_to == 'category' and not category:
            raise forms.ValidationError("Please select a category.")
        elif apply_to == 'subcategory' and not subcategory:
            raise forms.ValidationError("Please select a subcategory.")
        elif apply_to == 'product' and not product:
            raise forms.ValidationError("Please select a product.")

        return cleaned_data
from django import forms
from .models import Coupon

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
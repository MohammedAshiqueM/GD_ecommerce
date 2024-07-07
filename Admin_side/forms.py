from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code','discount_type', 'valid_from', 'valid_to', 'discount_value', 'active', 'min_purchase_amount','usage_limit','used_count','image','details']

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

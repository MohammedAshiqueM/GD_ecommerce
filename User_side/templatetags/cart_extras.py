# templatetags/cart_extras.py
from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    return value * arg

@register.filter
def calc_subtotal(cart_items):
    return sum(item.qty * item.product_configuration.price for item in cart_items)

@register.filter
def calc_total(cart_items):
    return calc_subtotal(cart_items) + 10  # assuming a flat shipping rate of $10

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='replace_space')
def replace_space(value, arg):
    """Replaces all spaces with the given argument."""
    return value.replace(' ', arg)
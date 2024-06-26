import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect,get_object_or_404
from .form import UserRegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.exceptions import ValidationError
from django.db.models import Q
from Admin_side.models import (
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


# from django.core.validators import validate_email,EmailValidator
import re
from .utils import generate_otp, send_otp
from datetime import datetime, timedelta


########################## function for login & singUp ###############################
@never_cache
def userLogin(request):
    # print("Submit value:", request.POST.get('submit'))

    if request.user.is_authenticated:
        return redirect('userHome')

    active_form = "login"  # Default active form
    print("Initial active_form:", active_form)

    def clean_email(email):
        mail_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if re.fullmatch(mail_regex, email):
            return email
        else:
            raise ValidationError("Invalid email format")

    def clean_password(password):
        if len(password) < 8:
            raise ValidationError("Password should contain at least 8 characters.")
        if not re.search("[A-Z]", password):
            raise ValidationError(
                "Password should contain at least one uppercase letter."
            )
        if not re.search("[a-z]", password):
            raise ValidationError(
                "Password should contain at least one lowercase letter."
            )
        if not re.search("[0-9]", password):
            raise ValidationError("Password should contain at least one digit.")
        if not re.search('[@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "Password should contain at least one special character."
            )
        return password

    if request.method == "POST":
        if request.POST.get("submit") == "login_form":
            ## login the user

            username = request.POST.get("loginUsername")
            password = request.POST.get("loginPassword")
            active_form = "login"

            if not username:
                messages.error(request, "Enter the Email")
            elif not password:
                messages.error(request, "Enter the Password")
            else:
                user = authenticate(username=username, password=password)
                if user is None:
                    messages.error(request, "Invalid Email Id or Password")
                elif user.is_active is False:
                    messages.error(request, f"{username} was temporarily blocked to access this site")
                else:
                    auth_login(request, user)
                    return redirect("userHome")

        elif request.POST.get("submit") == "signup_form":
            ## signUp new user

            signUp_username = request.POST["signupUsername"]
            signUp_email = request.POST["signupEmail"]
            signUp_password1 = request.POST["signupPassword"]
            signUp_password2 = request.POST["signupConfirmationPassword"]
            active_form = "signup"

            if User.objects.filter(username=signUp_username).exists():
                messages.error(
                    request, f"User name '{signUp_username}' is already taken"
                )
            elif User.objects.filter(email=signUp_email).exists():
                messages.error(
                    request, f"Mail Id '{signUp_email}' already has an account"
                )
            elif signUp_password1 != signUp_password2:
                messages.error(request, "Passwords do not match")
            else:
                if not signUp_username:
                    messages.error(request, "Enter the username")
                elif not signUp_email:
                    messages.error(request, "Enter the email")
                elif not signUp_password1:
                    messages.error(request, "Enter the Password")
                elif not signUp_password2:
                    messages.error(request, "Enter the Confirmation Password")
                else:

                    try:
                        clean_email(signUp_email)
                        clean_password(signUp_password1)
                    except ValidationError as e:
                        messages.error(request, e.message)
                    else:
                        # Save user data to session
                        request.session["username"] = signUp_username
                        request.session["email"] = signUp_email
                        request.session["password"] = signUp_password1

                        # Generate OTP and send it via email
                        otp = generate_otp()
                        send_otp(signUp_email, otp)
                        request.session["otp"] = otp
                        request.session["otp_creation_time"] = datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        return redirect("otp")
                        messages.success(
                            request, f"New user '{signUp_username}' is created"
                        )
                        return redirect("userLogin")

    print("Final active_form:", active_form)
    return render(request, "login.html", {"active_form": active_form})


def otp(request):
    # Retrieve user data from session
    username = request.session.get("username")
    email = request.session.get("email")
    password = request.session.get("password")
    otp_creation_time_str = request.session.get("otp_creation_time")

    # Check if user data is present in session
    if not (username and email and password):
        return redirect("userLogin")

    otp_creation_time = datetime.strptime(otp_creation_time_str, "%Y-%m-%d %H:%M:%S")
    otp_expiry_time = otp_creation_time + timedelta(minutes=5)

    if datetime.now() > otp_expiry_time:
        messages.error(request, "OTP has expired. Please sign up again.")
        return redirect("userLogin")

    if request.method == "POST":
        # Assuming your OTP fields are named 'ist', 'sec', 'third', 'fourth', and 'fifth'
        otp_digits = [
            request.POST.get("ist", ""),
            request.POST.get("sec", ""),
            request.POST.get("third", ""),
            request.POST.get("fourth", ""),
            request.POST.get("fifth", ""),
        ]

        # Concatenate OTP digits into a single OTP string
        otp = "".join(otp_digits)
        print("otp", otp)
        # Retrieve OTP from session
        session_otp = request.session.get("otp")
        print("session", otp)
        if otp == session_otp:
            # OTP is correct, create user and log in
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            user.is_active = True
            user.save()
            # auth_login(request, user)
            return redirect("userLogin")
        else:
            # Invalid OTP, display error message
            messages.error(request, "Ivalid otp")
            return render(request, "otp.html")

    return render(request, "otp.html")


def resend_otp(request):
    if request.method == "GET":
        # Retrieve user email from session
        email = request.session.get("email")

        # Generate new OTP and update session
        new_otp = generate_otp()
        request.session["otp"] = new_otp
        request.session["otp_creation_time"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Resend OTP via email (assuming send_otp function sends the OTP)
        send_otp(email, new_otp)

        # Display success message
        messages.success(request, "OTP has been resent.")

        # Redirect back to OTP page
        return redirect("otp")


########################## function for home page ############################
@login_required(login_url='userLogin')
@never_cache
def userHome(request):
    # if request.user.is_authenticated:
    categories = Category.objects.all()
    context = {"categories":categories}
    return render(request, "home.html",context)


def productDetails(request, pk):
    product = get_object_or_404(Product, pk=pk)
    related = Product.objects.filter(
        Q(category=product.category) | Q(subcategory=product.subcategory), 
        is_active=True
    ).exclude(id=product.id)
    
    configurations = []
    for config in product.configurations.all():
        option_ids = list(config.variation_options.values_list('id', flat=True))
        configurations.append({
            'id': config.id,
            'price': config.price,
            'qty_in_stock': config.qty_in_stock,
            'options': option_ids
        })
    
    if not product.is_active:
        return redirect("userHome")
    
    context = {
        "product": product,
        "related": related,
        'configurations': configurations
    }
    return render(request, "productDetails.html", context)

def shop(request):
    product = Product.objects.filter(is_active=True)
    context = {"product": product}
    return render(request, "shop.html", context)

def categoryProduct(request,pk):
    products = Product.objects.filter(category_id=pk)
    context = {"product":products}
    return render(request,"categoryProduct.html",context)

def subcategoryProduct(request,pk):
    products = Product.objects.filter(subcategory_id=pk)
    context = {"product":products}
    return render(request,"subcategoryProduct.html",context)

def profile(request, pk):
    user = get_object_or_404(User, pk=pk)
    addresses = Address.objects.filter(user=user)
    context = {"user": user, "addresses": addresses}
    return render(request, "profile.html", context)

def editProfile(request,pk):
    user = get_object_or_404(User, pk=pk)
    context = {"user":user}
    return render(request,"editProfile.html",context)

def addAddress(request,pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        unit_number = request.POST.get('unit_number')
        street_number = request.POST.get('street_number')
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2')
        city = request.POST.get('city')
        region = request.POST.get('region')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        is_default = request.POST.get('is_default') == 'on'

        # Validate required fields
        if not street_number or not address_line1 or not city or not region or not postal_code or not country:
            messages.error(request, "Please fill in all required fields.")
            return redirect('addAddress', pk=user.pk)
        else:
            if is_default:
                # Unset the default flag for all other addresses of the user
                Address.objects.filter(user=user, is_default=True).update(is_default=False)
        # Create the address
        Address.objects.create(
            user=user,
            unit_number=unit_number,
            street_number=street_number,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            region=region,
            postal_code=postal_code,
            country=country,
            is_default=is_default
        )
        messages.success(request, "Address added successfully.")
        return redirect('profile', pk=user.pk)  # Change to the appropriate success URL

    return render(request, 'addAddress.html', {'user': user})

def set_default_address(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        address_id = data.get('address_id')
        user_id = data.get('user_id')

        try:
            user = User.objects.get(pk=user_id)
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
            Address.objects.filter(pk=address_id).update(is_default=True)
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User does not exist'})
        except Address.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Address does not exist'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def editAddress(request, pk):
    try:
        address = get_object_or_404(Address, pk=pk, user=request.user)
        addresses = list(Address.objects.filter(user=request.user))
        address_number = addresses.index(address) + 1
        context = {"address": address, "edit": True,"address_number":address_number}
    except Address.DoesNotExist:
        messages.error(request, "The address you are trying to edit does not exist.")
        return redirect("profile", pk=request.user.pk) 
    if request.method == "POST":
        address.unit_number = request.POST.get('unit_number')
        address.street_number = request.POST.get('street_number')
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2')
        address.city = request.POST.get('city')
        address.region = request.POST.get('region')
        address.postal_code = request.POST.get('postal_code')
        address.country = request.POST.get('country')
        address.is_default = 'is_default' in request.POST
        address.save()
        messages.success(request, "Address updated successfully.")
        return redirect('profile', pk=request.user.pk)
    return render(request, "editAddress.html", context)

def deleteAddress(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if address.is_default:
        messages.error(request, "Default address cannot be deleted.")
        return redirect('profile', pk=request.user.id)
    if request.method == "POST":
        address.delete()
        messages.success(request, "Address deleted successfully.")
    return redirect('profile', pk=request.user.id)

def checkOut(request):
    return render(request, "checkOut.html")


def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    print('cart',cart)
    cart_items = CartItem.objects.filter(cart=cart)
    context = {
        'cart_items': cart_items
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_items_data = []
        for item in cart_items:
            item_data = {
                'id': item.id,
                'product_name': item.product_configuration.product.name,
                'product_image': item.product_configuration.product.images.first().image.url,
                'price': item.product_configuration.price,
                'quantity': item.qty
            }
            cart_items_data.append(item_data)
        
        return JsonResponse({'cart_items': cart_items_data})
    
    return render(request, 'cart.html', context)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

@require_POST
def get_configuration_id(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        selected_options = data.get('selected_options', [])

        if not product_id or not selected_options:
            raise ValueError('Product ID and selected options are required')

        product = get_object_or_404(Product, id=product_id)
        configuration = ProductConfiguration.objects.filter(
            product=product,
            variation_options__id__in=selected_options
        ).distinct().first()

        if not configuration:
            raise ValueError('Product configuration not found')

        return JsonResponse({'success': True, 'configuration_id': configuration.id}, status=200)
    
    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)}, status=400)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
@login_required
def add_to_cart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        configuration_id = data.get('configuration_id')
        quantity = data.get('quantity', 1)

        if not product_id or not configuration_id:
            raise ValueError('Product ID and configuration ID are required')

        product = get_object_or_404(Product, id=product_id)
        configuration = get_object_or_404(ProductConfiguration, id=configuration_id,product=product)

        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_configuration=configuration
        )

        if created:
            cart_item.qty = int(quantity)
        else:
            cart_item.qty += int(quantity)
        
        cart_item.save()

        return JsonResponse({'success': True}, status=200)
    
    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)}, status=400)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def contact(request):
    return render(request, "contact.html")



@require_POST
def get_product_combination(request, product_id):
    data = json.loads(request.body)
    product = Product.objects.get(id=product_id)
    selected_options = [VariationOption.objects.get(id=option_id) for option_id in data.values()]

    try:
        configuration = ProductConfiguration.objects.filter(
            product=product, 
            variation_options__in=selected_options
        ).distinct().get()
        response = {
            'price': configuration.price,
            'qty_in_stock': configuration.qty_in_stock,
        }
    except ProductConfiguration.DoesNotExist:
        response = {
            'price': product.price,
            'qty_in_stock': product.qty_in_stock,
        }

    return JsonResponse(response)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def calculate_subtotal_and_total(cart):
    cart_items = CartItem.objects.filter(cart=cart)
    subtotal = sum(item.qty * item.product_configuration.price for item in cart_items)
    shipping = 10  # Assuming a fixed shipping cost
    total = subtotal + shipping
    return subtotal, total

@csrf_exempt
@require_POST
def increment_quantity(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.qty += 1
        cart_item.save()
        
        cart = cart_item.cart
        subtotal, total = calculate_subtotal_and_total(cart)

        item_data = {
            'quantity': cart_item.qty,
            'price': cart_item.product_configuration.price,
            'total': cart_item.qty * cart_item.product_configuration.price,
            'subtotal': subtotal,
            'total_cart': total
        }
        return JsonResponse({'status': 'success', **item_data})
    except CartItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

@csrf_exempt
@require_POST
def decrement_quantity(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id)
        if cart_item.qty > 1:
            cart_item.qty -= 1
            cart_item.save()
        
        cart = cart_item.cart
        subtotal, total = calculate_subtotal_and_total(cart)

        item_data = {
            'quantity': cart_item.qty,
            'price': cart_item.product_configuration.price,
            'total': cart_item.qty * cart_item.product_configuration.price,
            'subtotal': subtotal,
            'total_cart': total
        }
        return JsonResponse({'status': 'success', **item_data})
    except CartItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

@csrf_exempt
@require_POST
def remove_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()
        return JsonResponse({'status': 'success'})
    except CartItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)


########################## function for logout ############################
def logout(request):
    auth_logout(request)
    return redirect("userLogin")

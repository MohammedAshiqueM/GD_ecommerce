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
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models import Count,Avg,Sum
import re
from .utils import generate_otp, send_otp
from datetime import datetime, timedelta
from django.db.models import Avg, Min, Max,Q
from django.conf import settings
import razorpay
from razorpay import Client as RazorpayClient
from django.utils import timezone
from django.db import transaction
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
    Coupon,
    CouponUsage,
    Wishlist,
    WishlistItem
)


# from django.core.validators import validate_email,EmailValidator


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
def common(request):
    categories = Category.objects.all()
    context = {"categories":categories}
    return redirect(request,'common.html',context)

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
        Q(subcategory=product.subcategory), 
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
    categories = Category.objects.all()
    context = {"product": product,"categories":categories}
    return render(request, "shop.html", context)

def categoryProduct(request,pk):
    products = Product.objects.filter(category_id=pk)
    sort = request.GET.get('sort', 'default')
    
    if sort == 'price_low_high':
        products = products.annotate(min_price=Min('configurations__price')).order_by('min_price')
    elif sort == 'price_high_low':
        products = products.annotate(max_price=Max('configurations__price')).order_by('-max_price')
    elif sort == 'featured':
        products = products.order_by('-is_featured') 
    elif sort == 'new_arrivals':
        products = products.order_by('-created_at') 
    elif sort == 'a_z':
        products = products.order_by('name')
    elif sort == 'z_a':
        products = products.order_by('-name')
    
    product_avg_prices = {}
    for product in products:
        avg_price = product.configurations.aggregate(Avg('price'))['price__avg']
        product_avg_prices[product.id] = avg_price
        
    context = {
        
        "products":products,
        "product_avg_prices": product_avg_prices,
        "sort": sort,
        }
    return render(request,"categoryProduct.html",context)



def subcategoryProduct(request, pk):
    products = Product.objects.filter(subcategory_id=pk)
    sort = request.GET.get('sort', 'default')
    categories = Category.objects.all()
    
    if sort == 'price_low_high':
        products = products.annotate(min_price=Min('configurations__price')).order_by('min_price')
    elif sort == 'price_high_low':
        products = products.annotate(max_price=Max('configurations__price')).order_by('-max_price')
    elif sort == 'featured':
        products = products.order_by('-is_featured') 
    elif sort == 'new_arrivals':
        products = products.order_by('-created_at') 
    elif sort == 'a_z':
        products = products.order_by('name')
    elif sort == 'z_a':
        products = products.order_by('-name')
    
    product_avg_prices = {}
    for product in products:
        avg_price = product.configurations.aggregate(Avg('price'))['price__avg']
        product_avg_prices[product.id] = avg_price
        
    context = {
        "products":products,
        "product_avg_prices": product_avg_prices,
        "sort": sort,
        "categories":categories
        }

    return render(request, "subcategoryProduct.html", context)


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


def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    print('cart',cart)
    cart_items = CartItem.objects.filter(cart=cart)
    categories = Category.objects.all()
    context = {
        'cart_items': cart_items,
        "categories":categories
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
    

@require_POST
def get_configuration_id(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        selected_options = data.get('selected_options', [])
        print("data", data)
        print("product id", product_id)
        print("selected options", selected_options)
        
        if not product_id or not selected_options:
            raise ValueError('Product ID and selected options are required')

        product = get_object_or_404(Product, id=product_id)
        print("product", product)
        
        # Convert selected options to VariationOption objects
        selected_options_objects = VariationOption.objects.filter(id__in=selected_options)
        print("selected option objects", selected_options_objects)
        
        # Ensure the number of selected options matches the expected number
        if len(selected_options_objects) != len(selected_options):
            raise ValueError('Mismatch in the number of selected options and the variation options found')

        # Fetch the configuration that exactly matches all selected options
        configurations = ProductConfiguration.objects.filter(
            product=product
        ).annotate(
            num_options=Count('variation_options')
        ).filter(
            num_options=len(selected_options)
        ).distinct()

        # Ensure the configuration matches the selected options exactly
        matching_configurations = []
        for config in configurations:
            config_option_ids = set(config.variation_options.values_list('id', flat=True))
            selected_option_ids = set(selected_options_objects.values_list('id', flat=True))
            if config_option_ids == selected_option_ids:
                matching_configurations.append(config)
        
        print("matching configurations", matching_configurations)
        
        if len(matching_configurations) == 1:
            configuration = matching_configurations[0]
            return JsonResponse({
                'success': True, 
                'configuration_id': configuration.id,
                'price': configuration.price,
                'qty_in_stock': configuration.qty_in_stock
            }, status=200)
        else:
            raise ValueError('No matching configuration found or multiple configurations found')

    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)}, status=400)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def contact(request):
    return render(request, "contact.html")


@csrf_exempt
@require_POST
def increment_quantity(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id)
        # if cart_item.product_configuration.qty_in_stock > cart_item.qty:
        cart_item.qty += 1
        cart_item.save()
        response_data = {
            'status': 'success',
            'quantity': cart_item.qty,
            'price': cart_item.product_configuration.price,
            'total': cart_item.qty * cart_item.product_configuration.price,
            'subtotal': calculate_subtotal(cart_item.cart),
            'total_cart': calculate_total(cart_item.cart)
        }
        # else:
        #     response_data = {'status': 'error', 'message': 'Insufficient stock'}
        return JsonResponse(response_data)
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
        response_data = {
            'status': 'success',
            'quantity': cart_item.qty,
            'price': cart_item.product_configuration.price,
            'total': cart_item.qty * cart_item.product_configuration.price,
            'subtotal': calculate_subtotal(cart_item.cart),
            'total_cart': calculate_total(cart_item.cart)
        }
        return JsonResponse(response_data)
    except CartItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

@csrf_exempt
@require_POST
def remove_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()
        response_data = {
            'status': 'success',
            'subtotal': calculate_subtotal(cart_item.cart),
            'total_cart': calculate_total(cart_item.cart)
        }
        return JsonResponse(response_data)
    except CartItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)

def calculate_subtotal(cart):
    cart_items = CartItem.objects.filter(cart=cart)
    return sum(item.qty * item.product_configuration.price for item in cart_items)

def calculate_total(cart):
    # Assuming shipping cost is fixed at $10
    return calculate_subtotal(cart) + 10


@require_POST
def check_cart_quantity(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        configuration_id = data.get('configuration_id')
        quantity = data.get('quantity')

        if not product_id or not configuration_id or quantity is None:
            return JsonResponse({'success': False, 'message': 'Product ID, Configuration ID, and quantity are required'}, status=400)

        # Fetch product configuration
        product_configuration = get_object_or_404(ProductConfiguration, id=configuration_id)
        
        # Calculate the total quantity in the cart for this configuration
        total_quantity_in_cart = CartItem.objects.filter(
            product_configuration_id=configuration_id
        ).aggregate(total=Sum('qty'))['total'] or 0

        # Check if adding the requested quantity exceeds the available stock
        # if total_quantity_in_cart + quantity > product_configuration.qty_in_stock:
        #     return JsonResponse({
        #         'success': False,
        #         'message': f'Only {product_configuration.qty_in_stock - total_quantity_in_cart} items available.'
        #     }, status=200)
        
        return JsonResponse({'success': True}, status=200)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@login_required
def order_success(request):
    return render(request, 'order_success.html')

@csrf_exempt
def razorpay_checkout(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            
            if amount is None:
                return JsonResponse({'error': 'Amount is required'}, status=400)
            
            # Convert amount to paise
            order_amount = int(float(amount) * 100)
            
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))
            
            order_currency = 'INR'
            order_receipt = 'order_rcptid_11'
            notes = {'Shipping address': 'Bommanahalli, Bangalore'}

            razorpay_order = client.order.create(
                {
                    'amount': order_amount,
                    'currency': order_currency,
                    'receipt': order_receipt,
                    'notes': notes,
                }
            )

            print('Razorpay order created:', razorpay_order) 
            return JsonResponse({
                'razorpay_order_id': razorpay_order['id'],
                'amount': order_amount
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error in razorpay_checkout: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def checkOut(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        # Retrieve the payment method
        payment_method = request.POST.get('payment')
        try:
            if payment_method == 'directcheck':
                payment_method_instance = PaymentMethod.objects.get(name='Cash On Delivery')
            elif payment_method == 'paypal':
                payment_method_instance = PaymentMethod.objects.get(name='Paypal')
            elif payment_method == 'banktransfer':
                payment_method_instance = PaymentMethod.objects.get(name='Bank Transfer')
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid payment method.'})
        except PaymentMethod.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Payment method not found.'})

        # Get the default address
        addresses = Address.objects.filter(user=request.user)
        default_address = addresses.filter(is_default=True).first() or addresses.first()
        if not default_address:
            return JsonResponse({'status': 'error', 'message': 'No address found for user.'})

        # Retrieve the cart and its items
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        # Calculate order total
        order_total = sum(item.qty * item.product_configuration.price for item in cart_items) + 10  # +10 for shipping


        
        # Create order status
        order_status, created = OrderStatus.objects.get_or_create(status='Pending')

        # Create the order
        order = Order.objects.create(
            user=request.user,
            payment_method=payment_method_instance,
            shipping_address=default_address,
            shipping_method=ShippingMethod.objects.get(name='Standard'),  # Replace with actual logic if needed
            order_total=order_total,
            order_status=order_status
        )

        # Create order lines
        for item in cart_items:
            OrderLine.objects.create(
                order=order,
                product_configuration=item.product_configuration,
                qty=item.qty,
                price=item.product_configuration.price
            )

        # Clear the cart
        cart_items.delete()

        return redirect('order_success')

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first() or addresses.first()
    if not default_address:
        show_modal = True
    else:
        show_modal = False

    # Retrieve the cart and its items
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    context = {
        "addresses": addresses,
        "default_address": default_address,
        "cart_items": cart_items,
        "categories":categories,
        "edit": True,
        'show_modal': show_modal,
        'razorpay_key':settings.RAZORPAY_KEY
    }
    return render(request, "checkOut.html", context)

@csrf_exempt
def place_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = request.user
            payment_method_value = data.get('payment')
            confirmation = data.get('confirmation', False)
            coupon_code = data.get('coupon_code', None)
            print("coupon:", coupon_code)
            print("Received data:", data)
            print("the pay method: ", payment_method_value)

            if not payment_method_value:
                return JsonResponse({'status': 'error', 'message': 'Payment method is required.'})

            if payment_method_value == 'razorpay':
                print("yaaaaaaaaaaaaaaaaaaah inside")
                # Verify Razorpay payment
                razorpay_payment_id = data.get('razorpay_payment_id')
                razorpay_order_id = data.get('razorpay_order_id')
                razorpay_signature = data.get('razorpay_signature')

                # Implement Razorpay payment verification here
                expiry_date = datetime.now().date() + timedelta(days=365)

                # If verification is successful, create PaymentMethod for Razorpay
                payment_method = PaymentMethod.objects.create(
                    user=user,
                    payment_type=PaymentType.objects.get(value="razorpay"),
                    provider="Razorpay",
                    expiry_date=expiry_date,  # dynamically calculated expiry date
                    account_number=razorpay_payment_id,
                    is_default=False
                )
            # Create or get COD payment method
            elif payment_method_value == 'cod':
                payment_method = create_cod_payment_method(user)
            else:
                try:
                    payment_method = PaymentMethod.objects.get(id=payment_method_value)
                except PaymentMethod.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Invalid payment method.'})

            shipping_address_id = data.get('shipping_address_id')
            if not shipping_address_id:
                return JsonResponse({'status': 'error', 'message': 'Shipping address ID is required.'})

            # Fetch existing address based on address ID
            try:
                shipping_address = Address.objects.get(id=shipping_address_id, user=user)
            except Address.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid shipping address.'})

            # Calculate order total
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)
            order_total = sum(item.qty * item.product_configuration.price for item in cart_items) + 10  # Add fixed shipping cost

            # Check product configurations and quantities
            error_messages = []
            confirmation_required = False
            discount_value = Decimal(0)  # Initialize discount_value

            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    if coupon.is_valid(order_total, request.user):
                        # Check if the user has already used the coupon

                        # Apply coupon discount
                        discount_value = Decimal(coupon.discount_value)
                        if coupon.discount_type == 'percentage':
                            print(discount_value)
                            discount_value = (discount_value / Decimal('100')) * Decimal(order_total)
                            print(discount_value)
                        order_total = Decimal(order_total) - discount_value
                        logger.info(f"Coupon applied. Discount: {discount_value}, New total: {order_total}")
                    # else:
                    #     user_coupon_usage = CouponUsage.objects.filter(coupon=coupon, user=user).count()
                    #     # if user_coupon_usage >= coupon.usage_limit:
                    #     #     return JsonResponse({'status': 'error', 'message': 'You have already used this coupon the maximum number of times.'})
                    #     # logger.warning(f"Invalid coupon attempted: {coupon_code}")
                    #     return JsonResponse({'status': 'error', 'message': 'This coupon is not valid.'})
                except Coupon.DoesNotExist:
                    logger.warning(f"Non-existent coupon code attempted: {coupon_code}")
                    return JsonResponse({'status': 'error', 'message': 'Invalid coupon code.'})
                except Exception as e:
                    logger.error(f"Error processing coupon {coupon_code}: {str(e)}")
                    return JsonResponse({'status': 'error', 'message': f'Error processing coupon: {str(e)}'})

            with transaction.atomic():
                for item in cart_items:
                    product_config = item.product_configuration
                    requested_qty = item.qty

                    if product_config.qty_in_stock == 0:
                        variation_options = ', '.join(option.value for option in product_config.variation_options.all())
                        error_messages.append(
                            f'Out of stock for {product_config.product.name} ({variation_options}).'
                        )
                    elif product_config.qty_in_stock < requested_qty:
                        variation_options = ', '.join(option.value for option in product_config.variation_options.all())
                        error_messages.append(
                            f'Insufficient stock for {product_config.product.name} ({variation_options}). Requested: {requested_qty}, Available: {product_config.qty_in_stock}'
                        )
                        confirmation_required = True

            if error_messages:
                if any("Out of stock" in msg for msg in error_messages):
                    return JsonResponse({'status': 'error', 'messages': error_messages})
                else:
                    if confirmation_required and not confirmation:
                        return JsonResponse({'status': 'error', 'messages': error_messages, 'confirmation_required': True})
                    else:
                        # Adjust quantities based on available stock
                        for item in cart_items:
                            product_config = item.product_configuration
                            if product_config.qty_in_stock < item.qty:
                                item.qty = product_config.qty_in_stock
                                item.save()

            # Create or get the default order status
            order_status, created = OrderStatus.objects.get_or_create(status='Pending')

            # Create order
            order = Order.objects.create(
                user=user,
                payment_method=payment_method,
                shipping_address=shipping_address,
                shipping_method=ShippingMethod.objects.first(),  # Replace with actual logic if needed
                order_total=order_total,
                order_status=order_status,
                discount_amount=discount_value
            )

            # Create order lines and update stock
            for item in cart_items:
                product_config = item.product_configuration
                if product_config.qty_in_stock < item.qty:
                    item.qty = product_config.qty_in_stock  # Adjust to available stock

                OrderLine.objects.create(
                    order=order,
                    product_configuration=product_config,
                    qty=item.qty,
                    price=product_config.price
                )

                # Update stock
                product_config.qty_in_stock -= item.qty
                product_config.save()

            # Optionally, clear the cart after placing the order
            cart_items.delete()

            return JsonResponse({'status': 'success', 'message': 'Order placed successfully.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

def verify_razorpay_payment(payment_id, order_id, signature):
    client = RazorpayClient(auth=(settings.RAZORPAY_KEY, settings.RAZORPAY_SECRET))
    try:
        return client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
    except Exception as e:
        print(f"Razorpay verification error: {str(e)}")
        return False
    
def create_cod_payment_method(user):
    cod_payment_type = PaymentType.objects.get(value="Cash on Delivery")

    # Calculate expiry date as 365 days from today
    expiry_date = datetime.now().date() + timedelta(days=365)

    payment_method, created = PaymentMethod.objects.get_or_create(
        user=user,
        payment_type=cod_payment_type,
        defaults={
            'provider': "N/A",  # or any default value
            'account_number': "N/A",  # or any default value
            'expiry_date': expiry_date,  # dynamically calculated expiry date
            'is_default': False
        }
    )
    return payment_method

def view_coupons(request):
    now = timezone.now()
    all_coupons = Coupon.objects.all()
    for coupon in all_coupons:
        coupon.is_expired = now > coupon.valid_to or not coupon.active
    return render(request, 'viewCoupon.html', {'coupons': all_coupons})

def test_view(request):
    return JsonResponse({'message': 'Test successful'})

@login_required
def wishlist(request):
    try:
        user_wishlist = Wishlist.objects.get(user=request.user)
        wishlist_items = WishlistItem.objects.filter(wishlist=user_wishlist)
    except Wishlist.DoesNotExist:
        wishlist_items = []

    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, "wishlist.html", context)

@login_required
@require_POST
def add_to_wishlist(request):
    data = json.loads(request.body)
    product_id = data.get('product_id')
    configuration_id = data.get('configuration_id')

    try:
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        product_config = ProductConfiguration.objects.get(id=configuration_id)
        
        wishlist_item, created = WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product_configuration=product_config
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@require_POST
@login_required
def remove_from_wishlist(request, item_id):
    try:
        logger.info(f"Attempting to remove item {item_id} for user {request.user}")
        item = WishlistItem.objects.get(id=item_id,  wishlist__user=request.user)
        item.delete()
        logger.info(f"Successfully removed item {item_id}")
        return JsonResponse({'success': True})
    except WishlistItem.DoesNotExist:
        logger.warning(f"Item {item_id} not found in wishlist for user {request.user}")
        return JsonResponse({'success': False, 'error': 'Item not found in wishlist'}, status=404)
    except Exception as e:
        logger.error(f"Error removing item {item_id}: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
from decimal import Decimal
import logging
from django.core.exceptions import ObjectDoesNotExist
logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def apply_coupon(request):
    try:
        data = json.loads(request.body)
        code = data.get('code')
        order_total = Decimal(data.get('order_total', '0'))

        logger.info(f"Received data: {data}")
        logger.info(f"Coupon code: {code}")
        logger.info(f"Order total: {order_total}")

        if not code or order_total <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid coupon code or order total'}, status=400)

        try:
            coupon = Coupon.objects.get(code=code)
        except ObjectDoesNotExist:
            return JsonResponse({'success': False, 'message': 'Coupon not found'}, status=404)

        logger.info(f"Coupon found: {coupon}")

        # Check if the order total meets the minimum purchase amount
        if order_total < coupon.min_purchase_amount:
            return JsonResponse({
                'success': False, 
                'message': f'This coupon requires a minimum purchase of ${coupon.min_purchase_amount:.2f}'
            })

        if not coupon.is_valid(order_total,request.user):

            user_coupon_usage = CouponUsage.objects.filter(coupon=coupon, user=request.user).count()
            if user_coupon_usage >= coupon.usage_limit:
                return JsonResponse({'success': False, 'message': 'You have already used this coupon the maximum number of times.'})
            return JsonResponse({'success': False, 'message': 'This coupon is not valid.'})

        discount_value = Decimal(coupon.discount_value)
        if coupon.discount_type == 'percentage':
            print(discount_value)
            discount_value = (discount_value / Decimal('100')) * Decimal(order_total)
            print(discount_value)
        new_total = Decimal(order_total) - discount_value


        # new_total = order_total - discount_value

        logger.info(f"Discount value: {discount_value}")
        logger.info(f"New total: {new_total}")

        # Update coupon usage count
        coupon.usage_limit += 1
        coupon.save()

        # Create a CouponUsage record
        CouponUsage.objects.create(coupon=coupon, user=request.user)

        return JsonResponse({
            'success': True, 
            'message': f'Coupon applied! You saved ${discount_value:.2f}. New total is ${new_total:.2f}', 
            'new_total': str(new_total),
            'discount_value': str(discount_value)
        })

    except json.JSONDecodeError:
        logger.error("Invalid JSON data received")
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.exception(f"Error in apply_coupon: {str(e)}")
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    
def my_orders(request):
    categories = Category.objects.all()
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'orderline_set__product_configuration__product__images',
        'orderline_set__product_configuration__variation_options'
    )
    return render(request, "myOrders.html", {'orders': orders, 'categories': categories})

@csrf_exempt
def cancel_order(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.order_status.status == 'Pending':
            cancel_status, created = OrderStatus.objects.get_or_create(status='Cancelled')
            with transaction.atomic():
                for order_line in order.orderline_set.all():
                    product_config = get_product_configuration(order_line)

                    if product_config:
                        product_config.qty_in_stock += order_line.qty
                        product_config.save()
                    else:
                        raise Exception(f"Product configuration not found for order line {order_line.id}")

            order.order_status = cancel_status
            order.save()
            return JsonResponse({'message': 'Order cancelled successfully.'})
        else:
            return JsonResponse({'message': 'Order cannot be cancelled.'}, status=400)

    except Order.DoesNotExist:
        return JsonResponse({'message': 'Order not found.'}, status=404)

    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

def get_product_configuration(order_line):
    """
    Helper function to retrieve the ProductConfiguration for an OrderLine.
    """
    try:
        product_config = order_line.product_configuration
        if product_config:
            return product_config
        else:
            raise Exception(f"Product configuration not found for order line {order_line.id}")
    except Exception as e:
        raise Exception(f"Error retrieving product configuration: {str(e)}")


    
########################## function for logout ############################
def logout(request):
    auth_logout(request)
    return redirect("userLogin")

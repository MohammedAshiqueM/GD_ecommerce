from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, logout as auth_logout, authenticate
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.forms import CheckboxInput
from itertools import product as iter_product
from .forms import CouponForm,OfferForm,CarouselBannerForm,OfferBannerForm
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count,F,Avg
from django.utils import timezone
from datetime import timedelta,datetime
from openpyxl import Workbook
from .models import (
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
    Offer,
    CategoryOffer,
    SubcategoryOffer,
    ProductOffer,
    SalesReport,
    CarouselBanner,
    OfferBanner,
    PaymentStatus,
    Wallet,
    Transaction
)


# Create your views here.
@never_cache
def adminLogin(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        # if not User.objects.filter(email=username).exists():
        #     messages.error(request,'Account not found')
        #     print("1",messages.error)
        #     return redirect('adminLogin')
        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, "Invalid username or password")
            return redirect("adminLogin")
        elif user and user.is_superuser:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, f"{user} have no access to this page")
            return redirect("adminLogin")
    return render(request, "adminLogin.html")


from django.db.models import Sum, Count
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from .models import OrderLine, Product, SubCategory, Category
@login_required(login_url='adminLogin')
@never_cache

# from django.db.models.functions import TruncDay, TruncMonth, TruncYear
# from django.utils import timezone
# from datetime import timedelta
# import json

def dashboard(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have access to this page.")
    
    # Get top 10 selling products
    top_products = OrderLine.objects.values('product_configuration__product__name').annotate(
        total_sales=Sum('qty')
    ).order_by('-total_sales')[:10]
    
    # Get top 10 selling subcategories
    top_subcategories = OrderLine.objects.values('product_configuration__product__subcategory__name').annotate(
        total_sales=Sum('qty')
    ).order_by('-total_sales')[:10]
    
    # Get top 10 selling categories
    top_categories = OrderLine.objects.values('product_configuration__product__category__name').annotate(
        total_sales=Sum('qty')
    ).order_by('-total_sales')[:10]
    
    # Calculate income for the last week
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    total_income = OrderLine.objects.filter(order__order_date__range=(start_date, end_date)).aggregate(total_income=Sum('price'))['total_income'] or 0

    # Get initial sales data for chart (default to daily)
    filter_type = 'daily'
    sales_data = OrderLine.objects.filter(order__order_date__gte=timezone.now() - timedelta(days=30)).annotate(
        date=TruncDay('order__order_date')
    ).values('date').annotate(total_sales=Sum('price')).order_by('date')

    formatted_sales_data = [
        {
            'date': item['date'].strftime('%Y-%m-%d'),
            'total_sales': float(item['total_sales'])
        }
        for item in sales_data
    ]

    context = {
        "top_products": top_products,
        "top_subcategories": top_subcategories,
        "top_categories": top_categories,
        "user_count": User.objects.count(),
        "order_count": Order.objects.count(),
        "product_count": Product.objects.count(),
        "total_income": total_income,
        "sales_data": json.dumps(formatted_sales_data),
        "filter_type": filter_type,
    }
    
    return render(request, "dashboard.html", context)

def get_sales_data(request):
    filter_type = request.GET.get('filter', 'daily')

    if filter_type == 'yearly':
        sales_data = OrderLine.objects.annotate(
            date=TruncYear('order__order_date')
        ).values('date').annotate(total_sales=Sum('price')).order_by('date')
    elif filter_type == 'monthly':
        sales_data = OrderLine.objects.annotate(
            date=TruncMonth('order__order_date')
        ).values('date').annotate(total_sales=Sum('price')).order_by('date')
    else:  # daily
        thirty_days_ago = timezone.now() - timedelta(days=30)
        sales_data = OrderLine.objects.filter(order__order_date__gte=thirty_days_ago).annotate(
            date=TruncDay('order__order_date')
        ).values('date').annotate(total_sales=Sum('price')).order_by('date')

    formatted_sales_data = [
        {
            'date': item['date'].strftime('%Y-%m-%d'),
            'total_sales': float(item['total_sales'])
        }
        for item in sales_data
    ]
    
    return JsonResponse(formatted_sales_data, safe=False)
def customers(request):
    if "value" in request.GET:
        credential = request.GET["value"]
        data = User.objects.filter(
            Q(username__icontains=credential) | Q(email__icontains=credential)
        )
        context = {"data": data}
    else:
        data = User.objects.all()
        context = {"data": data}
    return render(request, "customers.html", context)

def block(request, pk):
    try:
        user = User.objects.get(pk=pk)
        user.is_active = False
        user.save()
        return JsonResponse({"success": True})
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"})
    except Exception as e:
        return JsonResponse({"success": False, "error": "Internal server error"})

def unblock(request, pk):
    try:
        user = User.objects.get(pk=pk)
        user.is_active = True
        user.save()
        return JsonResponse({"success": True})
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"})
    except Exception as e:
        return JsonResponse({"success": False, "error": "Internal server error"})

def category(request):
    if "value" in request.GET:
        credential = request.GET["value"]
        parent = Category.objects.filter(Q(name__icontains=credential))
        sub = SubCategory.objects.filter(
            Q(name__icontains=credential) | Q(category__name__icontains=credential)
        )
        context = {"parent": parent, "sub": sub}
    else:
        parent = Category.objects.all()
        sub = SubCategory.objects.all()
        context = {"parent": parent, "sub": sub}
    return render(request, "category.html", context)

def addCategory(request):
    data = Category.objects.all()
    if request.method == "POST":
        print("outside")
        if request.POST.get("submit") == "main":
            print("inside")
            category = request.POST.get("categoryName")
            category_image = request.FILES.get('categoryImage')
            
            print(category)
            if not category or not category_image:
                messages.error(request, "Please fill in all required fields.")
                return redirect("addCategory")
            elif len(category) < 3:
                messages.error(request, "Category name must have atleast 3 letters")
                return redirect("addCategory")
            elif Category.objects.filter(name = category).exists():
                messages.error(request, "Category already exists")
                return redirect("addCategory")
            else:
                newCategory = Category.objects.create(name=category,category_image=category_image)
                newCategory.save()
                messages.success(request, f"New cagetory {newCategory} is created")
            return redirect("category")
        elif request.POST.get("submit") == "sub":
            sub_category = request.POST.get("subCategory")
            selected = request.POST.get("parentCategory")
            print(sub_category, selected)
            if not sub_category:
                messages.error(request, "Enter a Subcategory name")
                return redirect("addCategory")
            elif len(sub_category) < 3:
                messages.error(request, "Subcategory name must have atleast 3 letters")
                return redirect("addCategory")
            elif not selected:
                messages.error(
                    request,
                    f"Should select one parent class for subclass {sub_category}",
                )
                return redirect("addCategory")
            else:
                parent = Category.objects.get(id=selected)
                if SubCategory.objects.filter(name=sub_category, category=parent).exists():
                    messages.error(
                        request,
                        f"Sub category {sub_category} already exist in {parent.name}",
                    )
                    return redirect("addCategory")
                newSub = SubCategory.objects.create(name=sub_category, category=parent)
                newSub.save()
                messages.success(request, f"New Sub Cagetory {newSub} is created")
            return redirect("category")
    return render(request, "addCategory.html", {"data": data})

def editCategory(request, pk):
    data = Category.objects.get(pk=pk)
    context = {"value": data, "edit_mode": True}
    if request.method == "POST":
        category = request.POST.get("categoryName")
        category_image = request.FILES.get('categoryImage')
        print(category)
        if not category:
            messages.error(request, "Enter a Category name")
            return redirect("addCategory")
        elif len(category) < 3:
            messages.error(request, "Category name must have atleast 3 letters")
            return redirect("addCategory")
        else:
            data.name = category
            data.category_image = category_image
            data.save()
            messages.success(request, f"Category {category} has been updated")
        return redirect("category")
    return render(request, "editCategory.html", context)

def editSubcategory(request, pk):
    subcategory = SubCategory.objects.get(pk=pk)
    categories = Category.objects.all()
    if request.method == "POST":
        sub_category = request.POST.get("subCategory")
        selected = request.POST.get("parentCategory")
        print(sub_category, selected)
        if not sub_category:
            messages.error(request, "Enter a Subcategory name")
            return redirect("addCategory")
        elif len(sub_category) < 3:
            messages.error(request, "Subcategory name must have atleast 3 letters")
            return redirect("addCategory")
        elif not selected:
            messages.error(
                request, f"Should select one parent class for subclass {sub_category}"
            )
            return redirect("addCategory")
        else:
            parent = Category.objects.get(id=selected)
            subcategory.name = sub_category
            subcategory.category = parent
            subcategory.save()
            messages.success(
                request, f"Subcategory {subcategory.name} has been updated"
            )
        return redirect("category")
    context = {"value": subcategory, "data": categories, "edit_mode": True}
    return render(request, "editSubcategory.html", context)

def blockCategory(request, pk):
    try:
        category = get_object_or_404(Category, pk=pk)
        category.is_active = False
        category.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def unblockCategory(request, pk):
    try:
        category = get_object_or_404(Category, pk=pk)
        category.is_active = True
        category.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def blockSubcategory(request, pk):
    try:
        subcategory = get_object_or_404(SubCategory, pk=pk)
        subcategory.is_active = False
        subcategory.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def unblockSubcategory(request, pk):
    try:
        subcategory = get_object_or_404(SubCategory, pk=pk)
        subcategory.is_active = True
        subcategory.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    
def product(request):
    if "value" in request.GET:
        credential = request.GET["value"]
        data = Product.objects.filter(Q(name__icontains=credential))
        context = {"data": data}
    else:
        data = Product.objects.all()
        context = {"data": data}
    data = Product.objects.all()
    return render(request,"product.html",context)

def productAbout(request,pk):
    data = Product.objects.get(pk=pk)
    context = {"product": data}
    return render(request,"productAbout.html",context)

def addProduct(request):
    basecategory = Category.objects.all()
    context = {"base": basecategory, "edit_mode": False}
    
    if request.method == 'POST':
        name = request.POST.get("productName")
        category_id = request.POST.get("category")
        subcategory_id = request.POST.get("subcategory")
        sku = request.POST.get("sku")
        description = request.POST.get("description")
        productImages = request.FILES.getlist("productImage")
        
        if not name or not description or not category_id or not sku or not subcategory_id:
            messages.error(request, "Please fill in all required fields.")
            return redirect('addProduct')
        
        if not productImages or len(productImages) < 3:
            messages.error(request, "You must upload at least 3 images.")
            return redirect('addProduct')
        
        if Product.objects.filter(SKU=sku).exists():
            messages.error(request, f"Stock Keeping Unit {sku} already exists")
            return redirect('addProduct')
        
        # Validate category and subcategory
        try:
            category = Category.objects.get(id=category_id)
            subcategory = SubCategory.objects.get(id=subcategory_id)
        except Category.DoesNotExist or SubCategory.DoesNotExist:
            messages.error(request, "Selected category or subcategory does not exist.")
            return redirect('addProduct')
        
        # Save user data to sessiony
        # Create Product instance
        # Create an instance of the Product model without saving it to the database
        product = Product.objects.create(
            name=name,
            description=description,
            category=category,
            subcategory=subcategory,
            SKU=sku,
            is_active=True
        )


        # Save product images
        for image in productImages:
            cropped_image = crop_image(image)
            ProductImage.objects.create(product=product, image=cropped_image)

        # messages.success(request, "Product variation added successfully.")
        return redirect('variant',pk=product.pk)  # Redirect to product list or another view

       
    return render(request, "addProduct.html", context)


def adminLogout(request):
    auth_logout(request)
    return redirect("adminLogin")

def variant(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        variation_data = {}

        # Print the entire POST data for debugging
        print("POST data received:", request.POST)

        # Process variation names and options
        for key in request.POST:
            values = request.POST.getlist(key)
            if key.startswith('variation_name_'):
                index = key.split('_')[-1]
                variation_data[index] = {'name': values[0], 'options': []}
            elif key.startswith('variationOption_'):
                index = key.split('_')[1].split('[')[0]
                if index in variation_data:
                    variation_data[index]['options'].extend(values)


        # Print parsed variation data for debugging
        print("Parsed variation data:", variation_data)

        # Validate and save variations and options
        for index, data in variation_data.items():
            variation_name = data['name']
            variation_options = data['options']

            if not variation_name or not variation_options:
                messages.error(request, "Please fill in all required fields.")
                return redirect('variant', pk=product.pk)

            if len(variation_name) < 3:
                messages.error(request, "Variation name must have at least 3 letters.")
                return redirect('variant', pk=product.pk)

            if Variation.objects.filter(product=product, name=variation_name).exists():
                messages.error(request, f"Variation {variation_name} already exists for {product}.")
                return redirect('variant', pk=product.pk)

            variation = Variation.objects.create(product=product, name=variation_name)

            for option_value in variation_options:
                VariationOption.objects.create(variation=variation, value=option_value)

        messages.success(request, "Product variations added successfully.")
        return redirect('productConfiguration', pk=product.pk)

    return render(request, "variant.html", {'product': product})

def generate_combinations(variations):
    variation_options = [variation.variationoption_set.all() for variation in variations]
    return list(iter_product(*variation_options))

def productConfiguration(request, pk):
    product = get_object_or_404(Product, pk=pk)
    variations = product.variation_set.all()

    if request.method == 'POST':
        # Retrieve selected combinations from checkboxes
        selected_combinations = request.POST.getlist('selected_combinations')

        if not selected_combinations:
            messages.error(request, "Please select at least one combination.")
            return redirect('productConfiguration', pk=product.pk)

        # Delete existing configurations
        ProductConfiguration.objects.filter(product=product).delete()

        for index in selected_combinations:
            combination = generate_combinations(variations)[int(index)]

            # Create a list of VariationOption objects for the current combination
            variation_options = []
            for option in combination:
                variation_options.append(option)

            # Retrieve price and stock for this combination
            price = request.POST.get(f'price_{index}')
            qty_in_stock = request.POST.get(f'stock_{index}')

            if not price or not qty_in_stock:
                messages.error(request, "Please fill in all required fields.")
                return redirect('productConfiguration', pk=product.pk)

            try:
                price = float(price)
                qty_in_stock = int(qty_in_stock)
            except ValueError:
                messages.error(request, "Invalid price or stock value.")
                return redirect('productConfiguration', pk=product.pk)

            # Create the ProductConfiguration instance
            configuration = ProductConfiguration.objects.create(
                product=product,
                price=price,
                qty_in_stock=qty_in_stock
            )

            # Add variation_options to the ProductConfiguration
            configuration.variation_options.set(variation_options)

        messages.success(request, "Product configurations updated successfully.")
        return redirect('product')

    combinations = generate_combinations(variations)
    existing_configurations = ProductConfiguration.objects.filter(product=product).prefetch_related('variation_options')

    # Create a dictionary to store existing configuration data
    existing_config_data = {}
    for config in existing_configurations:
        key = tuple(sorted(option.id for option in config.variation_options.all()))
        existing_config_data[key] = {
            'price': config.price,
            'qty_in_stock': config.qty_in_stock
        }

    # Prepare combinations with existing data
    prepared_combinations = []
    for index, combination in enumerate(combinations):
        key = tuple(sorted(option.id for option in combination))
        existing_data = existing_config_data.get(key, {'price': '', 'qty_in_stock': ''})
        prepared_combinations.append({
            'index': index,
            'combination': combination,
            'price': existing_data['price'],
            'qty_in_stock': existing_data['qty_in_stock'],
            'is_existing': key in existing_config_data
        })

    context = {
        'product': product,
        'combinations': prepared_combinations
    }
    return render(request, 'productConfiguration.html', context)

def edit_configuration(request, configuration_id):
    configuration = get_object_or_404(ProductConfiguration, pk=configuration_id)

    if request.method == 'POST':
        price = request.POST.get('price')
        qty_in_stock = request.POST.get('qty_in_stock')

        if not price or not qty_in_stock:
            # Handle error - Missing fields
            return render(request, 'edit_configuration.html', {'configuration': configuration})

        configuration.price = price
        configuration.qty_in_stock = qty_in_stock
        configuration.save()

        return redirect('variation_combination', product_id=configuration.product.id)

    context = {
        'configuration': configuration,
    }
    return render(request, 'edit_configuration.html', context)

def crop_image(image_file):
    image = Image.open(image_file)
    # Define the crop box (left, upper, right, lower) - adjust as needed
    crop_box = (0, 0, min(image.size), min(image.size))
    cropped_image = image.crop(crop_box)
    cropped_image_io = BytesIO()
    cropped_image.save(cropped_image_io, format=image.format)
    cropped_image_file = ContentFile(cropped_image_io.getvalue(), name=image_file.name)
    return cropped_image_file

def get_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)


def blockProduct(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
        product.is_active = False
        product.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def unblockProduct(request, pk):
    try:
        product = get_object_or_404(Product, pk=pk)
        product.is_active = True
        product.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    
# @csrf_exempt
def toggle_featured(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body)
        product.is_featured = data.get('is_featured', False)
        product.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def editProduct(request, pk):
    product = get_object_or_404(Product, id=pk)
    basecategory = Category.objects.all()
    subcategories = SubCategory.objects.filter(category=product.category)
    product_images = ProductImage.objects.filter(product=product)
    
    # Initialize a list to store images marked for deletion
    images_to_delete = []

    if request.method == 'POST':
        product.name = request.POST.get("productName")
        category_id = request.POST.get("category")
        subcategory_id = request.POST.get("subcategory")
        product.SKU = request.POST.get("sku")
        product.description = request.POST.get("description")
        productImage = request.FILES.getlist("productImage")
        
        if not all([product.name, product.description, category_id, product.SKU, subcategory_id]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('editProduct', pk=pk)
        
        # Count selected checkboxes for deletion
        delete_image_ids = [int(key.split('_')[-1]) for key in request.POST if key.startswith('delete_image_')]
        selected_images_count = len(delete_image_ids)
        
        image_count = ProductImage.objects.filter(product=product).count()
        # Process checkboxes to mark images for deletion
        for image in product_images:
            if request.POST.get(f"delete_image_{image.id}") == "on":
                if selected_images_count > 0 and product_images.count() - selected_images_count < 3:
                    messages.error(request, "You must have at least 3 images. Cannot delete to drop below this limit.")
                    return redirect('editProduct', pk=pk)
                else:
                    images_to_delete.append(image)
        
        
        # Ensure at least 3 images are uploaded if adding new images
        if image_count + len(productImage) < 3:
            messages.error(request, "You must upload at least 3 images.")
            return redirect('editProduct', pk=pk)
        
        if Product.objects.filter(SKU=product.SKU).exclude(id=pk).exists():
            messages.error(request, f"Stock Keeping Unit {product.SKU} already exists")
            return redirect('editProduct', pk=pk)
        
        product.category = get_object_or_404(Category, id=category_id)
        product.subcategory = get_object_or_404(SubCategory, id=subcategory_id)
        product.save()
        
        # Delete marked images
        for image in images_to_delete:
            image.delete()
        
        # Save new/updated images
        for image in productImage:
            ProductImage.objects.create(product=product, image=image)

        messages.success(request, "Product updated successfully.")
        return redirect('productAbout',pk=product.pk)

    # Add a checkbox to each image in the context for deletion
    for image in product_images:
        image.delete_checkbox = CheckboxInput()

    context = {
        "base": basecategory,
        "subcategories": subcategories,
        "edit_mode": True,
        "product": product,
        "product_images": product_images,
    }
    return render(request, "addProduct.html", context)

def editvariant(request, pk):
    product = get_object_or_404(Product, id=pk)
    variations = product.variation_set.all().prefetch_related('variationoption_set')
    variation_options = []

    for variation in variations:
        options = variation.variationoption_set.all()
        in_use = product.has_combination_with_variation(variation.id)
        variation_options.append((variation, options, in_use))

    if request.method == 'POST':
        variation_ids = request.POST.getlist("variation_id")
        variation_names = request.POST.getlist("variation_name")
        variation_options_lists = [request.POST.getlist(f"variationOption_{i}") for i in range(len(variation_names))]

        # Handle new variations
        new_variation_names = [v for k, v in request.POST.items() if k.startswith("new_variation_name_")]
        new_variation_options = {}
        for k, v in request.POST.items():
            if k.startswith("new_variationOption_"):
                index = k.split("_")[-1]
                if index not in new_variation_options:
                    new_variation_options[index] = []
                new_variation_options[index].append(v)

        # Validate input
        if not all(variation_names + new_variation_names):
            messages.error(request, "Please provide names for all variations.")
            return redirect('editvariant', pk=product.pk)

        if not all(variation_options_lists + list(new_variation_options.values())):
            messages.error(request, "Please provide at least one option for each variation.")
            return redirect('editvariant', pk=product.pk)

        existing_variation_ids = [str(variation.id) for variation in variations]

        # Process existing variations and options
        for i, variation_id in enumerate(variation_ids):
            if variation_id:  # Existing variation
                variation = get_object_or_404(Variation, id=variation_id, product=product)
                variation.name = variation_names[i]
                variation.save()

                # Handle options
                existing_options = list(variation.variationoption_set.all())
                existing_option_values = [option.value for option in existing_options]
                new_option_values = variation_options_lists[i]

                # Delete removed options
                options_to_delete = [option for option in existing_options if option.value not in new_option_values]
                for option in options_to_delete:
                    ProductConfiguration.objects.filter(variation_options=option).delete()
                VariationOption.objects.filter(id__in=[option.id for option in options_to_delete]).delete()

                # Update or create options
                new_options = []
                updated_options = []
                for option_value in new_option_values:
                    if option_value not in existing_option_values:
                        new_options.append(VariationOption(variation=variation, value=option_value))
                    else:
                        option = next((opt for opt in existing_options if opt.value == option_value), None)
                        if option:
                            option.value = option_value
                            updated_options.append(option)

                VariationOption.objects.bulk_create(new_options)
                VariationOption.objects.bulk_update(updated_options, ['value'])

        # Create new variations
        for i, new_variation_name in enumerate(new_variation_names):
            new_variation = Variation.objects.create(product=product, name=new_variation_name)
            new_options = [VariationOption(variation=new_variation, value=value) 
                           for value in new_variation_options[f"new_{i}"]]
            VariationOption.objects.bulk_create(new_options)

        # Delete removed variations
        variations_to_delete = [vid for vid in existing_variation_ids if vid not in variation_ids]
        for variation_id in variations_to_delete:
            variation = Variation.objects.get(id=variation_id)
            if product.has_combination_with_variation(variation_id):
                ProductConfiguration.objects.filter(variation_options__variation=variation).delete()
            variation.delete()

        messages.success(request, "Product variations updated successfully.")
        return redirect('productConfiguration', pk=product.pk)

    context = {
        "edit_mode": True,
        "product": product,
        "variation_options": variation_options,
    }
    return render(request, "editvariant.html", context)

from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Order, OrderStatus, PaymentStatus

import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist

logger = logging.getLogger(__name__)

def orders(request):
    try:
        orders = Order.objects.all().order_by('-id')

        order_status = request.GET.get('order_status')
        payment_status = request.GET.get('payment_status')

        if order_status:
            orders = orders.filter(order_status__status=order_status)
        if payment_status:
            orders = orders.filter(payment_status__status=payment_status)

        order_statuses = OrderStatus.objects.values_list('status', flat=True).distinct()
        payment_statuses = PaymentStatus.objects.values_list('status', flat=True).distinct()

        context = {
            'orders': orders,
            'order_statuses': order_statuses,
            'payment_statuses': payment_statuses,
            'selected_order_status': order_status,
            'selected_payment_status': payment_status,
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                rows_html = render_to_string('orders.html', context, request=request)
                return JsonResponse({'rows_html': rows_html})
            except TemplateDoesNotExist:
                return JsonResponse({'error': 'Template orders_table_rows.html not found'}, status=500)
            except Exception as e:
                logger.error(f"Error rendering orders_table_rows.html: {str(e)}", exc_info=True)
                return JsonResponse({'error': 'Internal Server Error'}, status=500)

        return render(request, "orders.html", context)
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Internal Server Error'}, status=500)

def coupons(request):
    data = Coupon.objects.all()
    return render(request,"coupons.html",{"data":data})

def addCoupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('coupons')  # Redirect to the 'product' page after saving
    else:
        form = CouponForm()

    return render(request, 'addCoupon.html', {'form': form})

@require_POST
@csrf_protect
def toggle_coupon_status(request):
    data = json.loads(request.body)
    coupon_code = data.get('coupon_code')
    active = data.get('active')

    try:
        coupon = Coupon.objects.get(code=coupon_code)
        coupon.active = active
        coupon.save()
        return JsonResponse({'success': True})
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Coupon not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# def admin_orders(request):
#     orders = Order.objects.all()
#     context = {
#         'orders': orders
#     }
#     return render(request, 'admin_orders.html', context)

def change_order_status(request, order_id):
    status = request.GET.get('status')
    order = get_object_or_404(Order, id=order_id)

    if status:
        new_order_status, created = OrderStatus.objects.get_or_create(status=status)
        
        # Check if the new status is 'Cancelled'
        if status == 'Cancelled':
            # Process cancellation and potential refund
            process_cancellation(order)
        elif status == 'Delivered':
            # Check if payment is pending and update to complete
            if order.payment_status.status == 'Payment Pending':
                complete_status, created = PaymentStatus.objects.get_or_create(status='Payment Completed')
                order.payment_status = complete_status
                
        order.order_status = new_order_status
        order.save()
        return JsonResponse({
            'message': 'Order status changed successfully.',
            'order_status': new_order_status.status,
            'payment_status': order.payment_status.status
        })
    else:
        return JsonResponse({'message': 'Invalid status.'}, status=400)

def process_cancellation(order):
    # Check if the payment was completed
    if order.payment_status.status == 'Payment Completed':
        # Process refund
        wallet, created = Wallet.objects.get_or_create(user=order.user)
        refund_amount = order.order_total
        wallet.add_funds(refund_amount)
        
        # Create a refund transaction
        Transaction.objects.create(
            wallet=wallet,
            amount=refund_amount,
            transaction_type='REFUND',
            order=order
        )
        
        # Update payment status to 'Refunded'
        refunded_status, created = PaymentStatus.objects.get_or_create(status='Payment Refunded')
        order.payment_status = refunded_status
        order.save()
    
    # Update stock for each product configuration in the order
    for order_line in order.orderline_set.all():
        config = order_line.product_configuration
        config.qty_in_stock += order_line.qty
        config.save()

    
@login_required
def stock_management(request):
    products = Product.objects.prefetch_related('configurations__variation_options').all()
    return render(request, 'stockManagement.html', {'products': products})

@login_required
def update_stock(request):
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('config_'):
                config_id = key.replace('config_', '')
                try:
                    config = ProductConfiguration.objects.get(id=config_id)
                    config.qty_in_stock = int(value)
                    config.save()
                except (ProductConfiguration.DoesNotExist, ValueError):
                    pass
            elif key.startswith('price_'):
                config_id = key.replace('price_', '')
                try:
                    config = ProductConfiguration.objects.get(id=config_id)
                    config.price = float(value)
                    config.save()
                except (ProductConfiguration.DoesNotExist, ValueError):
                    pass
    return redirect('stock_management')

def offers(request):
    data = Offer.objects.all()
    return render(request,"offers.html",{"data":data})

def create_offer(request):
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save()
            apply_to = form.cleaned_data['apply_to']
            
            if apply_to == 'product':
                product_configuration = form.cleaned_data['product_configuration']
                ProductOffer.objects.create(proproduct_configuration=product_configuration, offer=offer)
            elif apply_to == 'category':
                category = form.cleaned_data['category']
                CategoryOffer.objects.create(category=category, offer=offer)
            elif apply_to == 'subcategory':
                subcategory = form.cleaned_data['subcategory']
                SubcategoryOffer.objects.create(subcategory=subcategory, offer=offer)
            
            return redirect('offers')  # Redirect to a list of offers
    else:
        form = OfferForm()
    
    return render(request, 'createOffers.html', {'form': form})

def get_product_configurations(request, product_id):
    configurations = ProductConfiguration.objects.filter(product_id=product_id).values('id', 'variation_options__variation__name', 'variation_options__value')
    
    config_list = []
    for config in configurations:
        config_name = ", ".join([f"{option['variation_options__variation__name']}: {option['variation_options__value']}" for option in configurations if option['id'] == config['id']])
        config_list.append({'id': config['id'], 'name': config_name})
    
    return JsonResponse({'configurations': config_list})

@require_POST
@csrf_protect
def toggle_offer_status(request):
    data = json.loads(request.body)
    getoffer = data.get('id')
    active = data.get('active')

    try:
        offer = Offer.objects.get(id=getoffer)
        offer.is_active = active
        offer.save()
        return JsonResponse({'success': True})
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Coupon not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import SalesReport, Order, OrderLine, ProductConfiguration
from django.http import HttpResponse, FileResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# @staff_member_required
def sales_report(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        # start_date = request.POST.get('start_date')
        # end_date = request.POST.get('end_date')

        if report_type == 'custom':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            # Convert string dates to datetime objects
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)
        elif report_type == 'daily':
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=1)
        elif report_type == 'weekly':
            start_date = timezone.now().date() - timedelta(days=7)
            end_date = timezone.now().date() + timedelta(days=1)
        elif report_type == 'monthly':
            start_date = timezone.now().date().replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1)
        elif report_type == 'yearly':
            start_date = timezone.now().date().replace(month=1, day=1)
            end_date = start_date.replace(year=start_date.year + 1)
        else:
            # Handle invalid report type
            return render(request, 'salesReport.html', {'error': 'Invalid report type'})

        orders = Order.objects.filter(order_date__gte=start_date, order_date__lt=end_date)
        total_sales = orders.aggregate(Sum('order_total'))['order_total__sum'] or 0
        total_orders = orders.count()
        total_discount = orders.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0
        
        product_sales = OrderLine.objects.filter(order__in=orders).values(
            'product_configuration__product__name',
            'product_configuration__id'
        ).annotate(
            total_quantity=Sum('qty'),
            total_sales=Sum('price')
        ).order_by('-total_quantity')
        
        for item in product_sales:
            config = ProductConfiguration.objects.get(id=item['product_configuration__id'])
            item['current_stock'] = config.qty_in_stock
            item['price'] = config.price
            item['variation_options'] = list(config.variation_options.all().values('variation__name', 'value'))


        report = SalesReport.objects.create(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            total_sales=total_sales,
            total_orders=total_orders,
            total_discount=total_discount
        )

        context = {
            'report': report,
            'orders': orders,
            'product_sales': product_sales,

        }
        return render(request, 'salesReport.html', context)

    return render(request, 'salesReport.html')



def export_excel(request, report_id):
    report = SalesReport.objects.get(id=report_id)
    orders = Order.objects.filter(order_date__gte=report.start_date, order_date__lt=report.end_date)
    product_sales = OrderLine.objects.filter(order__in=orders).values(
        'product_configuration__product__name',
        'product_configuration__id',
    ).annotate(
        total_quantity=Sum('qty'),
        total_sales=Sum(F('price') * F('qty')),
        avg_sold_price=Avg('price')
    ).order_by('-total_quantity')

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    # Add summary
    ws.append(["Sales Report", f"{report.start_date.date()} to {report.end_date.date()}"])
    ws.append(["Total Sales", report.total_sales])
    ws.append(["Total Orders", report.total_orders])
    ws.append(["Total Discount", report.total_discount])
    ws.append([])

    # Add product sales
    ws.append(["Product Sales"])
    headers = ['Product', 'Configuration', 'Avg Sold Price', 'Quantity Sold', 'Total Sales', 'Current Stock']
    ws.append(headers)

    for product in product_sales:
        config = ProductConfiguration.objects.get(id=product['product_configuration__id'])
        configuration = ", ".join([f"{opt.variation.name}: {opt.value}" for opt in config.variation_options.all()])
        ws.append([
            product['product_configuration__product__name'],
            configuration,
            round(product['avg_sold_price'], 2),
            product['total_quantity'],
            round(product['total_sales'], 2),
            config.qty_in_stock
        ])

    ws.append([])

    # Add order details
    ws.append(["Order Details"])
    headers = ['Order ID', 'Date', 'Total', 'Discount']
    ws.append(headers)

    for order in orders:
        ws.append([order.id, order.order_date, order.order_total, order.discount_amount])

    # Adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
        
    # Create http response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=sales_report_{report.start_date.date()}_{report.end_date.date()}.xlsx'

    wb.save(response)
    return response

from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from django.db.models import Sum, F, Avg

def export_pdf(request, report_id):
    report = SalesReport.objects.get(id=report_id)
    orders = Order.objects.filter(order_date__gte=report.start_date, order_date__lt=report.end_date)
    product_sales = OrderLine.objects.filter(order__in=orders).values(
        'product_configuration__product__name',
        'product_configuration__id',
    ).annotate(
        total_quantity=Sum('qty'),
        total_sales=Sum(F('price') * F('qty')),
        avg_sold_price=Avg('price')
    ).order_by('-total_quantity')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Sales Report: {report.start_date.date()} to {report.end_date.date()}", styles['Title']))

    # Summary data
    summary_data = [
        ["Total Sales", f"{report.total_sales}"],
        ["Total Orders", str(report.total_orders)],
        ["Total Discount", f"{report.total_discount}"]
    ]
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Product Sales", styles['Heading2']))

    # Product sales data
    product_data = [["Product", "Configuration", "Avg Sold Price", "Quantity Sold", "Total Sales", "Current Stock"]]
    for product in product_sales:
        config = ProductConfiguration.objects.get(id=product['product_configuration__id'])
        configuration = ", ".join([f"{opt.variation.name}: {opt.value}" for opt in config.variation_options.all()])
        product_data.append([
            product['product_configuration__product__name'],
            configuration,
            f"{round(product['avg_sold_price'], 2)}",
            str(product['total_quantity']),
            f"{round(product['total_sales'], 2)}",
            str(config.qty_in_stock)
        ])

    product_table = Table(product_data)
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(product_table)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Order Details", styles['Heading2']))

    # Order details data
    order_data = [["Order ID", "Date", "Total", "Discount"]]
    for order in orders:
        order_data.append([
            str(order.id),
            order.order_date.strftime('%Y-%m-%d'),
            f"{order.order_total}",
            f"{order.discount_amount}"
        ])

    order_table = Table(order_data)
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(order_table)

    # Build the PDF
    doc.build(elements)

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'sales_report_{report.start_date.date()}_{report.end_date.date()}.pdf')


def banner_list(request):
    carousel_banners = CarouselBanner.objects.all()
    offer_banners = OfferBanner.objects.all()
    return render(request, 'bannerList.html', {
        'carousel_banners': carousel_banners,
        'offer_banners': offer_banners
    })

def add_carousel_banner(request):
    if request.method == 'POST':
        form = CarouselBannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Carousel Banner added successfully.')
            return redirect('banner_list')
    else:
        form = CarouselBannerForm()
    return render(request, 'addCarouselBanner.html', {'form': form, 'banner_type': 'Carousel'})

def add_offer_banner(request):
    if request.method == 'POST':
        form = OfferBannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Offer Banner added successfully.')
            return redirect('banner_list')
    else:
        form = OfferBannerForm()
    return render(request, 'addOfferBanner.html', {'form': form, 'banner_type': 'Offer'})


def adminLogout(request):
    auth_logout(request)
    return redirect("adminLogin")
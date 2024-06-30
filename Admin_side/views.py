from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, logout as auth_logout, authenticate
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import ListView
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from itertools import product as iter_product
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
    ProductImage
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


@login_required(login_url='adminLogin')
@never_cache
def dashboard(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have access to this page.")
    if "value" in request.GET:
        credential = request.GET["value"]
        data = Product.objects.filter(Q(name__icontains=credential))
        user = User.objects.filter(
            Q(username__icontains=credential) | Q(email__icontains=credential)
        )
        context = {"data": data,"user":user}
    else:
        data = Product.objects.all()
        user = User.objects.all()
        context = {"data": data,"user":user}
    
    return render(request, "dashboard.html",context)

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

        messages.success(request, "Product configurations added successfully.")
        return redirect('product')

    combinations = generate_combinations(variations)
    context = {
        'product': product,
        'combinations': enumerate(combinations)  # Use enumerate to get index for checkbox values
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
    
from django.forms import CheckboxInput

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
    variations = product.variation_set.all()
    variation_options = []

    for variation in variations:
        options = variation.variationoption_set.all()
        in_use = product.has_combination_with_variation(variation.id)
        variation_options.append((variation, options, in_use))

    if request.method == 'POST':
        variation_ids = request.POST.getlist("variation_id")
        variation_names = request.POST.getlist("variation_name")
        variation_options_lists = [request.POST.getlist(f"variationOption_{i}") for i in range(len(variation_names))]

        # Validate input
        if not all(variation_names) or not all(variation_options_lists):
            messages.error(request, "Please fill in all required fields.")
            return redirect('editvariant', pk=product.pk)

        existing_variation_ids = [str(variation.id) for variation in variations]

        # Process existing variations and options
        for i, variation_id in enumerate(variation_ids):
            if variation_id:  # Existing variation
                variation = get_object_or_404(Variation, id=variation_id, product=product)
                variation.name = variation_names[i]
                variation.save()

                # Handle options
                existing_options = variation.variationoption_set.all()
                existing_option_values = [option.value for option in existing_options]
                new_option_values = variation_options_lists[i]

                # Delete removed options
                for option in existing_options:
                    if option.value not in new_option_values:
                        # Delete any product combinations that include this option
                        ProductConfiguration.objects.filter(variation_options=option).delete()
                        option.delete()

                # Update or create options
                for option_value in new_option_values:
                    if option_value not in existing_option_values:
                        VariationOption.objects.create(variation=variation, value=option_value)
                    else:
                        option = variation.variationoption_set.filter(value=option_value).first()
                        if option:
                            option.value = option_value
                            option.save()
            else:  # New variation
                variation = Variation.objects.create(product=product, name=variation_names[i])
                for option_value in variation_options_lists[i]:
                    VariationOption.objects.create(variation=variation, value=option_value)

        # Delete removed variations
        for variation_id in existing_variation_ids:
            if variation_id not in variation_ids:
                variation = Variation.objects.get(id=variation_id)
                if product.has_combination_with_variation(variation_id):
                    # Delete any product combinations that include this variation
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

def orders(request):
    orders = Order.objects.all()
    return render(request,"orders.html",{'orders': orders})

def adminLogout(request):
    auth_logout(request)
    return redirect("adminLogin")
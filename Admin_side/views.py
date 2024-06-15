from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
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


# @login_required(login_url='adminLogin')
# @never_cache
def dashboard(request):
    # if not request.user.is_superuser:
    #     return HttpResponseForbidden("You do not have access to this page.")
    return render(request, "dashboard.html")


def customers(request):
    if "value" in request.GET:
        credential = request.GET["value"]
        data = User.objects.filter(
            Q(username__icontains=credential) | Q(email__icontains=credential)
        )
        context = {"data": data}
    else:
        data = User.objects.all()
        print(f"SQL Query: {str(data.query)}")
        print(list(data))
        context = {"data": data}
        print(data)
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
            print(category)
            if not category:
                messages.error(request, "Enter a Category name")
                return redirect("addCategory")
            elif len(category) < 3:
                messages.error(request, "Category name must have atleast 3 letters")
                return redirect("addCategory")
            else:
                newCategory = Category.objects.create(name=category)
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
        print(category)
        if not category:
            messages.error(request, "Enter a Category name")
            return redirect("addCategory")
        elif len(category) < 3:
            messages.error(request, "Category name must have atleast 3 letters")
            return redirect("addCategory")
        else:
            data.name = category
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
    data = Product.objects.all()
    return render(request,"product.html",{"data":data})



def addProduct(request):
    basecategory = Category.objects.all()
    context = {"base": basecategory, "edit_mode": False}
    
    if request.method == 'POST':
        name = request.POST.get("productName")
        category_id = request.POST.get("category")
        subcategory_id = request.POST.get("subcategory")
        sku = request.POST.get("sku")
        stockQuantity = request.POST.get("stockQuantity")
        price = request.POST.get("price")
        description = request.POST.get("description")
        productImages = request.FILES.getlist("productImage")
        
        if not name or not description or not category_id or not sku or not stockQuantity or not price or not subcategory_id:
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
        
        # Create Product instance
        product = Product.objects.create(
            name=name,
            description=description,
            category=category,
            subcategory=subcategory,
            SKU=sku,
            qty_in_stock=stockQuantity,
            price=price,
            is_active=True
        )
    
        # Save product images
        for image in productImages:
            cropped_image = crop_image(image)
            ProductImage.objects.create(product=product, image=cropped_image)

        messages.success(request, "Product added successfully.")
        return redirect('product')
    
    return render(request, "addProduct.html", context)

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
        product.qty_in_stock = request.POST.get("stockQuantity")
        product.price = request.POST.get("price")
        product.description = request.POST.get("description")
        productImage = request.FILES.getlist("productImage")
        
        if not all([product.name, product.description, category_id, product.SKU, product.qty_in_stock, product.price, subcategory_id]):
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
        return redirect('product')

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

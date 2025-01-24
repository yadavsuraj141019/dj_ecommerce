from django.shortcuts import render,HttpResponse,HttpResponseRedirect,redirect
from django.shortcuts import render, get_object_or_404
from .models import Product, Cart, CartItem,Order, Address,ShippingMethod, PaymentMethod
from .forms import SignUpForm, LoginForm,AddressForm,ShippingMethodForm, PaymentMethodForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from decimal import Decimal
from django.http import Http404,HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction

# Home Page View Function

def home(request):
    products = Product.objects.all()
    return render(request, 'ecomm/home.html', {'products':products})



# Product Detail Page View Function

def product_detail(request,id):
     product = get_object_or_404(Product, id=id)
     if request.method == "POST":
        if request.user.is_authenticated:
             cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        else:
              cart, created = Cart.objects.get_or_create(user=None, is_active=True)
        
        if product.quantity_in_stock <= 0:
            messages.error(request, f"Sorry, {product.product_name} is out of stock.")
            return redirect('product_detail', id=id)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if created:
            cart_item.quantity = 1  # Set initial quantity to 1 if it's a new item
        else:
            # If product already exists in the cart, check the available stock
            if cart_item.quantity < product.quantity_in_stock:
                cart_item.quantity += 1  # Increase quantity
            else:
                messages.error(request, f"Sorry, you can't add more {product.product_name} to your cart. Not enough stock.")
                return redirect('product_detail', id=id)

        cart_item.save()   

        cart_url = reverse('cart')  # Assuming 'view_cart' is the name of your cart view URL
        
        message = f"{product.product_name} has been added to your cart! <a href='{cart_url}'>View Cart</a>"
        messages.success(request, message, extra_tags='safe')

        return redirect('product_detail', id=id)       

     return render(request, 'ecomm/product_detail.html', {'product':product})

    # get_object_or_404(Product, id=product_id) tries to fetch the product by its ID. If the product does not exist, Django will return a 404 error page.


# Product Listing Page View Function

def product_list(request):
    products = Product.objects.all()
    return render(request, 'ecomm/product_list.html', {'products': products})


# Add To Cart View Function

# def add_to_cart(request):
#     pass



# Registration View Function

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            messages.success(request, 'You Have Registered Your Account')
            user = form.save()
    else:
        form = SignUpForm()
    return render(request, 'ecomm/signup.html', {'form':form})



# Login View Function

def user_login(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
                form = LoginForm(request=request, data=request.POST)
                if form.is_valid():
                    uname = form.cleaned_data['username']
                    upass = form.cleaned_data['password']
                    user = authenticate(username= uname, password= upass)
                    if user is not None:
                        login(request, user)
                        messages.success(request, 'Logged in Successfully')
                        return HttpResponseRedirect('/')
        else:
            form = LoginForm()
            return render(request, 'ecomm/login.html', {'form':form})
    else:
        return HttpResponseRedirect('/')
    
# Logout View Function

def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


# Cart View Function

def cart_view(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        cart = Cart.objects.filter(user=None).first()

    if cart:
        cart_items = cart.items.all()
        total_price = sum(item.total_price() for item in cart_items)
    else:
        cart_items = []
        total_price = 0

    return render(request, 'ecomm/cart.html', {'cart': cart, 'cart_items': cart_items, 'total_price': total_price})


# Increment And Decrement Of Product Quantity In Cart Page View Function 

def update_cart(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id)
    product = cart_item.product

    if action == 'increase':
        # Check if there's enough stock to increase the quantity
        if cart_item.quantity < product.quantity_in_stock:
            cart_item.quantity += 1
            # cart_item.save()
        else:
            messages.error(request, f"Sorry, you can't add more {product.product_name} to your cart. Not enough stock.")
    elif action == 'decrease':
        # Decrease the quantity, but ensure it doesn't go below 1
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            # cart_item.save()
        else:
            messages.error(request, f"The quantity of {product.product_name} can't go below 1.")
    cart_item.save()

    return redirect('cart')  # Redirect to the cart view


# Checkout View Function

# def get_or_create_cart(user=None):
#     """
#     Get an existing cart or create a new one.
#     """
#     if user:
#         cart, created = Cart.objects.get_or_create(user=user)
#     else:
#         cart = Cart.objects.create()  # Anonymous user
#     return cart


# Remove From Cart View Function

def remove_from_cart(request, item_id):
    """
    Remove an item from the cart.
    """
    try:
        item = CartItem.objects.get(id=item_id)
        item.delete()
    except CartItem.DoesNotExist:
        raise Http404("Item not found")
    
    return redirect('cart')

@login_required
def checkout(request):
    # Fetch the user's active cart
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        # For guest users, create a cart associated with `None` as the user
        cart = Cart.objects.filter(user=None).first()

    shipping_methods = ShippingMethod.objects.all()
    payment_methods = PaymentMethod.objects.all()

    if not cart or cart.items.count() == 0:
        return redirect('cart')  # Redirect to cart if it's empty

    # Calculate the total price of the products in the cart
    total_price = sum(item.total_price() for item in cart.items.all())

    if request.method == 'POST':
        # Process billing and shipping addresses
        billing_address = Address.objects.create(
            user=request.user if request.user.is_authenticated else None,  # Use the logged-in user, or None for guest
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            street_address=request.POST.get('street_address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            zip_code=request.POST.get('zip_code'),
            country=request.POST.get('country'),
            phone=request.POST.get('phone')
        )

        shipping_address = Address.objects.create(
            user=request.user if request.user.is_authenticated else None,  # Use the logged-in user, or None for guest
            first_name=request.POST.get('shipping_first_name'),
            last_name=request.POST.get('shipping_last_name'),
            street_address=request.POST.get('shipping_street_address'),
            city=request.POST.get('shipping_city'),
            state=request.POST.get('shipping_state'),
            zip_code=request.POST.get('shipping_zip_code'),
            country=request.POST.get('shipping_country'),
            phone=request.POST.get('shipping_phone')
        )

        # Get the selected shipping method from the POST data
        shipping_method_id = request.POST.get('shipping_method')
        shipping_method = ShippingMethod.objects.get(id=shipping_method_id)

        # Get the selected payment method from the POST data
        payment_method_id = request.POST.get('payment_method')
        payment_method = PaymentMethod.objects.get(id=payment_method_id)

        # Calculate total price (base price + shipping cost)
        total_price += shipping_method.cost  # Add the shipping cost to the total price

        # Create the order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,  # Use the logged-in user, or None for guest
            total_price=total_price,
            billing_address=billing_address,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            payment_method=payment_method,
        )

        # Clear the cart after placing the order
        cart.items.all().delete()

        # Redirect to the order success page
        return redirect('order_success', order_id=order.id)

    return render(request, 'ecomm/checkout.html', {
        'cart': cart,
        'shipping_methods': shipping_methods,  # Pass shipping methods to template
        'payment_methods': payment_methods,    # Pass payment methods to template
        'total_price': total_price,  # Pass the total price (including cart items)
    })


@login_required
def order_success(request, order_id):
    
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'ecomm/order_success.html', {
        'order': order
    })

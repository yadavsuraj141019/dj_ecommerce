from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404


class Product(models.Model):
    product_name = models.CharField(max_length=100)
    product_description = models.TextField()
    product_price = models.IntegerField()
    quantity_in_stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)


    def __str__(self):
        return self.product_name
    

class Cart(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="cart", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, default='open')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Cart for {self.user.username}" if self.user else "Anonymous Cart"
    
    # def clear_cart(self):
    #     """Clears all items in the cart."""
    #     self.items.all().delete()  # This deletes all CartItem entries related to this cart

    def total_price(self):
        """Calculate the total price of all items in the cart."""
        return sum(item.product.price * item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}"

    def total_price(self):
        return self.product.product_price * self.quantity
    

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses", null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.street_address}"
    
class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - ${self.cost}"

# Payment Method Model
class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_address = models.ForeignKey(Address, related_name="billing_address", on_delete=models.SET_NULL, null=True)
    shipping_address = models.ForeignKey(Address, related_name="shipping_address", on_delete=models.SET_NULL, null=True)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_total_price(self):
        """Update the total price based on the shipping method."""
        self.total_price += self.shipping_method.cost
        self.save()

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"
    
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'order_success.html', {
        'order': order,
        'shipping_method': order.shipping_method,
        'payment_method': order.payment_method,
    })

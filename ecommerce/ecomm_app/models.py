from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

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
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Cart for {self.user.username}" if self.user else "Anonymous Cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}"

    def total_price(self):
        return self.product.product_price * self.quantity
    

class ShippingMethod(models.Model):
    STANDARD = 'standard'
    EXPRESS = 'express'

    SHIPPING_METHOD_CHOICES = [
        (STANDARD, 'Standard'),
        (EXPRESS, 'Express'),
    ]

    shipping_method = models.CharField(
        max_length=20,
        choices=SHIPPING_METHOD_CHOICES,
        default=STANDARD
    )

    def __str__(self):
        return self.shipping_method
    

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username}'s Shipping Address"
    

class PaymentMethod(models.Model):
    payment_method = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

# class BillingAddress(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     address_line1 = models.CharField(max_length=255)
#     address_line2 = models.CharField(max_length=255, blank=True, null=True)
#     city = models.CharField(max_length=100)
#     state = models.CharField(max_length=100)
#     postal_code = models.CharField(max_length=20)
#     country = models.CharField(max_length=100)

#     def __str__(self):
#         return f"{self.user.username}'s Billing Address"
    
class Order(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    # billing_address = models.ForeignKey(BillingAddress, on_delete=models.SET_NULL, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - User: {self.user.username}"

    def calculate_total(self):
        # Calculate the total price of items in the order
        item_total = sum(item.price for item in self.items.all())
        shipping_total = self.shipping_method.cost if self.shipping_method else 0
        self.total_price = item_total + shipping_total
        self.save()
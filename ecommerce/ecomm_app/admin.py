from django.contrib import admin
from .models import Product,CartItem,Cart,ShippingMethod,PaymentMethod,Order

class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'product_name', 'product_description', 'product_price', 'image']


admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ShippingMethod)
admin.site.register(PaymentMethod)
admin.site.register(Order)


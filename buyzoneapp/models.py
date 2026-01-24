from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator

from django.conf import settings   # ✅ ALWAYS USE THIS


class Contact(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    desc = models.TextField(max_length=500)
    phoneNo = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Product(models.Model):
    product_name = models.CharField(max_length=50)
    category = models.CharField(max_length=50, default="")
    subcategory = models.CharField(max_length=50, default="")
    price = models.IntegerField(default=0)
    OldPrice = models.IntegerField(default=0)
    Discount = models.IntegerField(default=0)
    desc = models.CharField(max_length=300)
    ShippingFee = models.IntegerField(default=0)
    Rating = models.IntegerField(default=0, validators=[MaxValueValidator(5)])
    image = models.ImageField(upload_to='shop/images/')

    def __str__(self):
        return f'{self.id} | {self.product_name}'


class Size(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.IntegerField(default=1)

    class Meta:
        unique_together = ('product', 'size')
    
    def __str__(self):
        return f"{self.product.id} | {self.product.product_name} | {self.size.name} | Stock: {self.stock}"

class Orders(models.Model):
    items_json = models.JSONField()
    name = models.CharField(max_length=90)
    email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)

    oid = models.CharField(max_length=100, blank=True, null=True)
    paymentstatus = models.CharField(max_length=30, default="Pending")
    amountpaid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    BookDate = models.DateTimeField(default=timezone.now)

    payment_id = models.CharField(max_length=255, null=True, blank=True)  # razorpay_payment_id
    refund_id = models.CharField(max_length=255, null=True, blank=True)
    is_refunded = models.BooleanField(default=False)

    delivered_at = models.DateTimeField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders'
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        
    def __str__(self):
        return f"Order #{self.id}"

#Proxy model for Cancelled & Paid Orders
class CancelledPaidOrder(Orders):
    class Meta:
        proxy = True
        verbose_name = "Refundable Orders"
        verbose_name_plural = "Refundable Orders"

class OrderUpdate(models.Model):
    order = models.ForeignKey(
        Orders,
        related_name="updates",
        on_delete=models.CASCADE
    )
    update_desc = models.TextField()
    delivered = models.BooleanField(default=False)
    update_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Update"
        verbose_name_plural = "Order Updates"

    def __str__(self):
        return f"Update for Order #{self.order.id}"
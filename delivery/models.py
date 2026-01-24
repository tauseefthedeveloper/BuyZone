from django.db import models

# Create your models here.
from django.contrib.auth.models import User 
from buyzoneapp.models import Orders
from django.utils import timezone
from datetime import timedelta

class DeliveryBoy(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Delivery Boy"
        verbose_name_plural = "Delivery Boys"

    def __str__(self):
        return self.user.username

class DeliveryOTP(models.Model):
    order = models.OneToOneField(Orders, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)


    class Meta:
        verbose_name = "Delivery OTP"
        verbose_name_plural = "Delivery OTPs"

    def __str__(self):
        return f"OTP for Order #{self.order.id}"

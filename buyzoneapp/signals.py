from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from .models import OrderUpdate


@receiver(post_save, sender=OrderUpdate)
def sync_order_on_update(sender, instance, created, **kwargs):
    order = instance.order

    # If admin marks order as delivered
    if instance.delivered:
        order.paymentstatus = "Paid"

        # If payment was COD or unpaid, mark amount as paid
        if order.amountpaid < order.amount:
            order.amountpaid = Decimal(order.amount)

        order.save()

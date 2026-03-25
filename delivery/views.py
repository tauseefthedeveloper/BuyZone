import json
import random
import threading
from django.shortcuts import render, redirect, get_object_or_404
from buyzoneapp.models import Orders, OrderUpdate
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.utils.timezone import localdate
from django.db.models import Sum

from helper import send_email_async
from .models import DeliveryOTP
from buyzoneapp.models import Orders, OrderUpdate, Product
from django.db.models import OuterRef, Exists, Q
from .utils.receipt import build_modern_invoice
from django.core.mail import send_mail



def delivery_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.groups.filter(name='DeliveryBoy').exists()
    )(view_func)


@login_required
@delivery_required
def generate_delivery_otp(request, order_id):
    order = get_object_or_404(Orders, id=order_id)

    otp = str(random.randint(100000, 999999))

    DeliveryOTP.objects.update_or_create(
        order=order,
        defaults={
            "otp": otp,
            "verified": False,
            "created_at": timezone.now()   # RESET expiry time
        }
    )


    subject = "Your BuyZone Delivery OTP"

    html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>BuyZone Delivery OTP</title>
        </head>

        <body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">

        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8; padding:20px 0;">
        <tr>
        <td align="center">

        <!-- Main Container -->
        <table width="600" cellpadding="0" cellspacing="0" 
        style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1);">

        <!-- Header -->
        <tr>
        <td style="background-color:#0d6efd; padding:25px; text-align:center;">
        <h1 style="color:#ffffff; margin:0; font-size:26px;">BuyZone</h1>
        <p style="color:#e9ecef; margin:5px 0 0; font-size:14px;">
            Secure Delivery Verification
        </p>
        </td>
        </tr>

        <!-- Body -->
        <tr>
        <td style="padding:30px; color:#333333;">

        <h2 style="margin-top:0;">Hi {order.name}, 👋</h2>

        <p style="font-size:15px; line-height:1.6;">
            Your delivery is on the way! To securely confirm your order delivery,
            please share the OTP below with your delivery partner.
        </p>

        <!-- OTP BOX -->
        <div style="text-align:center; margin:30px 0;">
            <div style="
            display:inline-block;
            background:#0d6efd;
            color:#ffffff;
            padding:14px 30px;
            font-size:26px;
            border-radius:10px;
            letter-spacing:6px;
            font-weight:bold;
            ">
            {otp}
            </div>

            <p style="font-size:13px; color:#6c757d; margin-top:10px;">
            This OTP is valid for 5 minutes. Do not share it with anyone else.
            </p>
        </div> <br>
        <p style="font-size:14px; line-height:1;">
            Total amount to be pay: <strong>₹ {order.amount}</strong>
        </p>
        <p style="font-size:14px; line-height:1;">
            Delivery for Order ID: <strong>{order.oid}</strong>
        </p>

        <p style="font-size:14px; line-height:1.6;">
            If you did not expect this delivery, please contact our support team immediately.
        </p>

        <p style="margin-top:30px; font-size:14px;">
            Regards,<br>
            <strong>BuyZone Team</strong>
        </p>

        </td>
        </tr>

        <!-- Footer -->
        <tr>
        <td style="background-color:#f8f9fa; padding:15px; text-align:center; font-size:12px; color:#6c757d;">
        © 2026 BuyZone. All rights reserved.
        </td>
        </tr>

        </table>

        </td>
        </tr>
        </table>

        </body>
        </html>
        """

        # Plain-text fallback (required for some clients)
    text_message = f"Your BuyZone Delivery OTP is {otp}. Do not share it with anyone."

    email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.email]
    )
    
    email.attach_alternative(html_message, "text/html")
    threading.Thread(target=send_email_async, args=(email,)).start()

    messages.success(request, "OTP sent to customer email")
    return redirect("verify_delivery_otp", order_id=order.id)


@login_required
@delivery_required
def verify_delivery_otp(request, order_id):
    order = get_object_or_404(Orders, id=order_id)
    delivery_otp = get_object_or_404(DeliveryOTP, order=order)
    

    if request.method == "POST":
        entered = request.POST.get("otp")

        if delivery_otp.is_expired():
            messages.error(request, "OTP expired. Generate a new one.")
            return redirect("generate_delivery_otp", order.id)

        if delivery_otp.otp == entered:

            delivery_otp.verified = True
            delivery_otp.save()

            otp = delivery_otp.otp
            subject = "Confirmation: Your BuyZone Order is Delivered"

            html_message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset="UTF-8">
                <title>BuyZone — Order Delivered</title>
                </head>

                <body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">

                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8; padding:20px 0;">
                <tr>
                <td align="center">

                <!-- Main Container -->
                <table width="600" cellpadding="0" cellspacing="0" 
                style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1);">

                <!-- Header -->
                <tr>
                <td style="background-color:#0d6efd; padding:25px; text-align:center;">
                <h1 style="color:#ffffff; margin:0; font-size:26px;">BuyZone</h1>
                <p style="color:#e9ecef; margin:5px 0 0; font-size:14px;">
                    Order Delivery Confirmation
                </p>
                </td>
                </tr>

                <!-- Body -->
                <tr>
                <td style="padding:30px; color:#333333;">

                <h2 style="margin-top:0;">Hi {order.name}, 🎉</h2>

                <p style="font-size:15px; line-height:1.6;">
                    We’re happy to let you know that your order has been successfully delivered.
                </p>

                <p style="font-size:15px; line-height:1.6;">
                    Thank you for shopping with <strong>BuyZone</strong>. We hope you enjoy your purchase!
                </p>

                <!-- Order Info box -->
                <div style="margin:25px 0; text-align:center;">
                    <table cellpadding="0" cellspacing="0" style="border:1px solid #e4e6eb; border-radius:10px; padding:15px; display:inline-block;">
                    <tr>
                        <td style="font-size:14px; color:#333;">
                        <strong>Order ID:</strong> {order.oid}
                        </td>
                    </tr>
                    <tr>
                        <td style="font-size:14px; color:#333;">
                        <strong>Status:</strong> Delivered ✔
                        </td>
                    </tr>
                    </table>
                </div>

                <p style="font-size:14px; line-height:1.6;">
                    If you did not receive this order or have any concerns, please contact our support team immediately.
                </p>

                <p style="margin-top:30px; font-size:14px;">
                    Warm Regards,<br>
                    <strong>BuyZone Team</strong>
                </p>

                </td>
                </tr>

                <!-- Footer -->
                <tr>
                <td style="background-color:#f8f9fa; padding:15px; text-align:center; font-size:12px; color:#6c757d;">
                © 2026 BuyZone. All rights reserved.
                </td>
                </tr>

                </table>

                </td>
                </tr>
                </table>

                </body>
                </html>
            """


            text_message = f"Order Delivered: Your BuyZone order with ID {order.oid} has been delivered successfully."

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.email]
            )

            order.paymentstatus = "Paid"
            order.amountpaid = order.amountpaid or order.amount
            order.delivered_at = timezone.now()
            order.save(update_fields=["paymentstatus","amountpaid"])

            email.attach_alternative(html_message, "text/html")

            pdf_buffer = build_modern_invoice(order)
            email.attach(
                filename=f"BuyZone_Invoice_{order.oid}.pdf",
                content=pdf_buffer.getvalue(),
                mimetype="application/pdf"
            )

            threading.Thread(target=send_email_async, args=(email,)).start()


            

            OrderUpdate.objects.create(
                order=order,
                update_desc="The order has been delivered successfully.",
                delivered=True
            )


            messages.success(request, "Delivery confirmed successfully")
            return redirect("delivery_dashboard")

        messages.error(request, "Incorrect OTP")

    return render(request, "delivery/verify.html", {"order": order})


@login_required
@delivery_required
def delivery_dashboard(request):

    delivered_updates = OrderUpdate.objects.filter(
        order=OuterRef('pk'), delivered=True
    )

    orders = Orders.objects.annotate(
        is_delivered=Exists(delivered_updates)
    ).filter(
        assigned_to=request.user,
        paymentstatus__in=["Pending", "Paid"],
        is_delivered=False,
        is_returned=False
    ).order_by('-id')

    for o in orders:
        try:
            o.items = json.loads(o.items_json or "{}")
        except:
            o.items = {}

    activity = (
        OrderUpdate.objects
        .filter(order__assigned_to=request.user)
        .filter(update_desc__icontains="Assigned")
        .select_related("order")
        .order_by('-update_date')
    )

    return render(request, "delivery/dashboard.html", {
        "orders": orders,
        "activity": activity
    })


@login_required
@delivery_required
def delivery_stats(request):
    user = request.user
    today = localdate()

    # Total assigned to this delivery boy
    total_assigned = Orders.objects.filter(
        assigned_to=user
    ).count()

    # Delivered (OTP verified)
    delivered_count = Orders.objects.filter(
        assigned_to=user,
        deliveryotp__verified=True
    ).count()

    # Pending (assigned but NOT delivered yet)
    pending_count = Orders.objects.filter(
        assigned_to=user
    ).exclude(
        paymentstatus="Cancelled"
    ).filter(
        Q(deliveryotp__verified=False) | Q(deliveryotp__isnull=True)
    ).distinct().count()

    # Delivered today
    today_delivered = Orders.objects.filter(
        assigned_to=user,
        deliveryotp__verified=True,
        deliveryotp__created_at__date=today
    ).count()

    # Cancelled orders (based on your field)
    cancelled_count = Orders.objects.filter(
        assigned_to=user,
        paymentstatus="Cancelled"
    ).count()

    # Total cash collected (based on amountpaid)
    cash_collected = Orders.objects.filter(
        assigned_to=user,
        deliveryotp__verified=True
    ).aggregate(total=Sum("amountpaid"))["total"] or 0

    # Last 10 assigned orders
    recent_orders = Orders.objects.filter(
        assigned_to=user,
        paymentstatus__in=["Pending", "Paid", "Cancelled"]
    ).order_by("-id")[:10]

    context = {
        "total_assigned": total_assigned,
        "delivered_count": delivered_count,
        "pending_count": pending_count,
        "today_delivered": today_delivered,
        "cancelled_count": cancelled_count,
        "cash_collected": cash_collected,
        "recent_orders": recent_orders,
    }

    return render(request, "delivery/stats.html", context)


@login_required
@delivery_required
def orderDetails(request, order_id):
    order = get_object_or_404(Orders, oid=order_id)

    updates = OrderUpdate.objects.filter(order=order).order_by('-update_date')

    items = json.loads(order.items_json)
    productIds = [int(str(pid).replace("pr","")) for pid in items.keys()]
    products = Product.objects.filter(id__in=productIds)

    images = {p.id: p.image.url for p in products if p.image}


    context = {
        "order": order,
        "updates": updates,
        "items": items,
        "images":images,
    }

    return render(request, "delivery/orderDetails.html", context)


@login_required
@delivery_required
def mark_return_picked(request, order_id):

    order = get_object_or_404(
        Orders,
        id=order_id,
        assigned_to=request.user
    )

    if not order.is_returned:
        messages.error(request, "This order is not marked for return.")
        return redirect("delivery_dashboard")

    order.delivered_at = timezone.now()
    order.assigned_to = None

    if order.payment_id:
        order.paymentstatus = "Cancelled"
        order.is_refunded = False
        order.save()

        OrderUpdate.objects.create(
            order=order,
            update_desc="Return picked. Refund will be processed after verification",
            delivered=False
        )

        send_mail(
            subject="Return picked – refund in progress",
            message=(
                f"Hi {order.name},\n\n"
                f"We’ve picked up your return for Order ID {order.oid}.\n\n"
                "Our team will verify the item and process your refund shortly.\n"
                "Refunds are usually completed within 5–7 business days.\n\n"
                "— BuyZone Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=True,
        )

    else:
        order.paymentstatus = "Return Completed"
        order.is_refunded = False
        order.save()

        OrderUpdate.objects.create(
            order=order,
            update_desc="Return picked successfully (COD order)",
            delivered=False
        )

        send_mail(
            subject="Return picked successfully",
            message=(
                f"Hi {order.name},\n\n"
                f"We’ve successfully picked up your return for Order ID {order.oid}.\n\n"
                "Since this was a Cash on Delivery order, the refund process is done our team within 5–7 business days.\n\n"
                "— BuyZone Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=True,
        )

    messages.success(request, "Return pickup completed successfully.")
    return redirect("return_dashboard")

@login_required
@delivery_required
def return_order_picked(request):
    user = request.user

    returns = Orders.objects.filter(
        assigned_to=user,
        is_returned=True
    ).order_by("-id")

    for o in returns:
        try:
            o.items = json.loads(o.items_json or "{}")
            print(json.loads(o.items_json or "{}"))
        except:
            o.items = {}

    activity = (
        OrderUpdate.objects
        .filter(order__assigned_to=user)
        .filter(update_desc__icontains="Return")
        .select_related("order")
        .order_by("-update_date")[:20]
    )
    return render(request, "delivery/return.html", {
        "returns": returns,
        "activity": activity
    })

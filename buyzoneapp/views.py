import email
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib import messages
from .models import Orders, OrderUpdate, Product, Contact, ProductVariant
from razorpay.errors import SignatureVerificationError
from django.conf import settings
import razorpay
from math import ceil
import time
from decimal import Decimal
import json
from django.http import JsonResponse
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
import json
from django.db import transaction
from django.utils.http import urlencode
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from datetime import timedelta



from django.http import JsonResponse

# Create your views here.
def index(request):
    allProds = []
    # get unique categories
    categories = Product.objects.values_list('category', flat=True).distinct()

    for cat in categories:
        products_qs = Product.objects.filter(category=cat)

        total_products = products_qs.count()

        # if more than 4 → pick 4 random
        if total_products > 4:
            products = products_qs.order_by('?')[:4]
        else:
            products = products_qs

        nSlides = ceil(len(products) / 4)

        allProds.append([products, range(1, nSlides + 1), nSlides])

    return render(request, "index.html", {'allProds': allProds})


def contact(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login first")
        return redirect('/auth/login/')
    
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        desc = request.POST.get('desc')
        phoneNo = request.POST.get('number')

        if not all([name, email, desc, phoneNo]):
            messages.error(request, "All fields are required.")
            return render(request, "contact.html")

        myquery = Contact(name=name, email=email, desc=desc, phoneNo=phoneNo)
        myquery.save()
        messages.info(request, 'We will get back to you soon!')
        return render(request, "contact.html")
    
    return render(request, "contact.html")

def about(request):
    return render(request, "about.html")

def sign(request):
    return render(request, "sign.html")


def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login first")
        return redirect('/auth/login/')

    items_json = request.POST.get('itemsJson') or request.GET.get('itemsJson')
    items = json.loads(items_json) if items_json else {}
    product_ids = [int(pid.replace("pr","")) for pid in items.keys()]

    products = Product.objects.filter(id__in=product_ids)

    variants_map = {}

    params = {"itemsJson": items_json}

    for p in products:
        variants = ProductVariant.objects.filter(product=p, stock__gt=0)
        variants_map[p.id] = list(
            variants.values("id","size__name","stock")
        )

    user = request.user
    previous_orders = Orders.objects.filter(email=user.email)

    address1 = address2 = city = state = zip_code = phone = ''

    if previous_orders.exists():
        last = previous_orders.last()
        address1 = last.address1
        address2 = last.address2
        city = last.city
        state = last.state
        zip_code = last.zip_code
        phone = last.phone

    if request.method == "POST":
        items_json = request.POST.get('itemsJson')
        cart = json.loads(items_json) if items_json else {}

        if not cart:
            messages.error(request,"Your cart is empty. Please add items before checkout.")
            return redirect(f"/checkout/?{urlencode(params)}")

        cart_items = []

        if isinstance(cart, dict):
            for pid, data in cart.items():

                # list format from localStorage
                if isinstance(data, list):
                    qty = int(data[0])
                    size = data[5] if len(data) > 5 else None

                else:
                    qty = int(data.get("qty",1))
                    size = data.get("size")

                cart_items.append({
                    "pid": int(str(pid).replace("pr","")),
                    "qty": qty,
                    "size": size,
                })




        elif isinstance(cart, list):
            for item in cart:
                if isinstance(item, dict):
                    cart_items.append({
                        "pid": int(item.get("pid")),
                        "qty": int(item.get("qty", 1)),
                        "size": item.get("size"),
                    })
                else:
                    cart_items.append({
                        "pid": int(item),
                        "qty": 1,
                        "size": None,
                    })


        for item in cart_items:
            pid = item["pid"]
            qty = item["qty"]
            size = item["size"]

            variants = ProductVariant.objects.filter(product_id=pid)

            if variants.exists():
                if not size:
                    messages.error(request, "Please select size for all size-based products.")
                    return redirect(f"/checkout/?{urlencode(params)}")

                try:
                    variant = ProductVariant.objects.get(product_id=pid, size__name=size)
                except ProductVariant.DoesNotExist:
                    messages.error(request, "Selected size not available.")
                    return redirect(f"/checkout/?{urlencode(params)}")

                if variant.stock < qty:
                    messages.error(request, f"{variant.product.product_name} ({size}) is out of stock.")
                    return redirect(f"/checkout/?{urlencode(params)}")

            else:
                size = None

        amount = Decimal(request.POST.get('amt') or "0")
        if amount <= 0:
            messages.error(request,"Invalid order amount.")
            return redirect(f"/checkout/?{urlencode(params)}")

        name = request.POST.get('name')
        email = request.POST.get('email')
        address1 = request.POST.get('address1')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        with transaction.atomic():
            order = Orders.objects.create(
                items_json=items_json,
                name=name,
                email=email,
                amount=amount,
                address1=address1,
                address2=address2,
                city=city,
                state=state,
                zip_code=zip_code,
                phone=phone
            )

            for item in cart_items:
                pid = item["pid"]
                qty = item["qty"]
                size = item["size"]

                variants = ProductVariant.objects.filter(product_id=pid)

                if variants.exists():
                    variant = ProductVariant.objects.get(product_id=pid, size__name=size)
                    variant.stock -= qty
                    variant.save()


            OrderUpdate.objects.create(order=order,update_desc="Order created. Waiting for payment.")

            if request.POST.get('payment_method') == "cod":
                order.oid = f"COD_{int(time.time())}"
                order.paymentstatus = "Pending"
                OrderUpdate.objects.create(order=order,update_desc="Order placed successfully with Cash on Delivery.")
                order.save()
                return render(request,'order_success.html',{'order':order})

            razorpay_order = client.order.create({"amount": int(amount*100),"currency":"INR"})
            order.oid = razorpay_order['id']
            order.paymentstatus = "Pending"
            order.amountpaid = amount

            OrderUpdate.objects.create(order=order,update_desc="Online payment initiated. Awaiting confirmation.")

            order.save()

            return render(request,"paytm.html",{
                "order_id": razorpay_order['id'],
                "key_id": settings.RAZORPAY_KEY_ID,
                "amount": int(amount*100),
                "order": order
            })

    return render(request,'checkout.html',{
        "OrderDetails":{
            "address1":address1,
            "address2":address2,
            "city":city,
            "state":state,
            "zip_code":zip_code,
            "phone":phone
        },
        "variants_map_json": json.dumps(variants_map)
    })


def order_activity(request, order_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login first")
        return redirect('/auth/login/')

    # Fetch order safely
    order = get_object_or_404(
        Orders,
        oid=order_id,
        email=request.user.email
    )

    # Parse items_json FIRST
    items = json.loads(order.items_json or "{}")

    products = []
    for pid, value in items.items():
        try:
            product = Product.objects.get(id=int(pid.replace("pr","")))
            products.append({
                "product": product,
                "quantity": value[0],
                "price": value[2],
                "size": value[5] if len(value) > 5 else None
            })
        except Product.DoesNotExist:
            continue

    updates = order.updates.order_by('-update_date')

    context = {
        "order": order,
        "products": products,
        "updates": updates
    }

    return render(request, 'order_activity.html', context)



def payment_status(request):
    status = request.GET.get('status', 'unknown')
    razorpay_order_id = request.GET.get('razorpay_order_id', '')
    razorpay_payment_id = request.GET.get('razorpay_payment_id', '')
    message = request.GET.get('message', '')
    order = get_object_or_404(Orders, oid=razorpay_order_id)

    if razorpay_payment_id:
        order.payment_id = razorpay_payment_id

    if status == 'success':
        order.paymentstatus = 'Paid'
        if not order.amountpaid:
            order.amountpaid = order.amount
        OrderUpdate.objects.create(
            order=order,
            update_desc="Payment received successfully."
        )
    elif status in ['failure', 'canceled']:
        order.paymentstatus = 'Cancelled'
        order.amountpaid = 0
        OrderUpdate.objects.create(
            order=order,
            update_desc="Payment cancelled by user during Razorpay checkout."
        )
    else:
        order.paymentstatus = 'Unknown'

    order.save()

    context = {
        'status': status,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'amount': order.amountpaid,
        'message': message,
    }

    return render(request, 'paymentstatus.html', context)


@csrf_exempt
def handlerequest(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})

    try:
        data = json.loads(request.body)

        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }

        if not all(params_dict.values()):
            return JsonResponse({'status': 'error', 'message': 'Missing payment data'})

        # VERIFY SIGNATURE
        client.utility.verify_payment_signature(params_dict)

        order = Orders.objects.filter(oid=params_dict['razorpay_order_id']).first()
        if not order:
            return JsonResponse({'status': 'error', 'message': 'Order not found'})

        order.paymentstatus = 'Paid'
        order.amountpaid = order.amount   # assuming rupees
        order.payment_id = params_dict['razorpay_payment_id']
        order.save()

        return JsonResponse({'status': 'success'})

    except SignatureVerificationError:
        order = Orders.objects.filter(oid=params_dict['razorpay_order_id']).first()
        if order:
            order.paymentstatus = "Failed"
            order.save()
            OrderUpdate.objects.create(
                order=order,
                update_desc="Payment failed or cancelled by user."
            )
        return JsonResponse({'status': 'error', 'message': 'Signature verification failed'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


def profile(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login first")
        return redirect('/auth/login/')

    user = request.user
    items = Orders.objects.filter(
        email=request.user.email
    ).select_related("assigned_to").prefetch_related("updates").order_by("-BookDate")
    # Decode items_json for each order
    for order in items:
        try:
            order.products = json.loads(order.items_json or '{}')  
            latest = order.updates.order_by('-update_date').first()
            if order.assigned_to and latest and not latest.delivered:
                latest.update_desc = "Out for Delivery"

        except Exception as e:
            order.products = []  # fallback if json invalid

        # ---------------------------------
    updates = OrderUpdate.objects.filter(order__in=items).order_by('-update_date').first()


    for order in items:
        if order.delivered_at:
            order.return_allowed = timezone.now() <= order.delivered_at + timedelta(days=5)
            order.return_allowed_date = order.delivered_at + timedelta(days=5)
        else:
            order.return_allowed = False
    context = {
        'items': items,
        'updates': updates
    }
    return render(request, 'profile.html', context)


def productDetails(request,product_id):
    product = get_object_or_404(Product,id=product_id)
    rating = min(product.Rating, 5)
    stars = list(range(1, rating + 1))
    return render(request,'productDetail.html',{ 'product': product,'stars':stars })


def category_products(request, category):
    products = Product.objects.filter(category=category)

    context = {
        'category': category,
        'products': products
    }
    return render(request, 'category_products.html', context)


def cancel_order(request, order_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login first")
        return redirect('/auth/login/')
    
    order = get_object_or_404(
        Orders,
        id=order_id,
        email=request.user.email
    )

    last_update = order.updates.last()
    if last_update and last_update.delivered:
        messages.error(request, "Delivered orders cannot be cancelled.")
        return redirect('profile')
    
    original_amount_paid = order.amountpaid

    order.paymentstatus = 'Cancelled'

    if original_amount_paid > 0:
        order.amountpaid = original_amount_paid
    else:
        order.amountpaid = 0
    order.save()

    try:
        cart = json.loads(order.items_json or "{}")

        if isinstance(cart, dict):
            for pid, data in cart.items():
                product_id = int(str(pid).replace("pr",""))

                # list format
                if isinstance(data, list):
                    qty = int(data[0])
                    size = data[5] if len(data) > 5 else None
                else:
                    qty = int(data.get("qty", 1))
                    size = data.get("size")

                if size:
                    try:
                        variant = ProductVariant.objects.get(product_id=product_id, size__name=size)
                        variant.stock += qty
                        variant.save()
                    except ProductVariant.DoesNotExist:
                        pass
    except Exception as e:
        print("STOCK RESTORE ERROR:", e)
        
    if last_update:
        last_update.update_desc = "The order has been cancelled by the user."
        last_update.delivered = False
        last_update.save()
    else:
        order.updates.create(
            update_desc="The order has been cancelled by the user.",
            delivered=False
        )

    prepaid_templates=f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>BuyZone — Order Cancelled</title>
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
        Order Cancellation Confirmation
        </p>
        </td>
        </tr>

        <!-- Body -->

        <tr>
        <td style="padding:30px; color:#333333;">

        <h2 style="margin-top:0;">Hi { order.name },</h2>

        <p style="font-size:15px; line-height:1.6;">
        We want to let you know that your order <strong>#{ order.oid }</strong> has been successfully cancelled as per your request.
        </p>

        <!-- Order Info box -->

        <div style="margin:25px 0; text-align:center;">
        <table cellpadding="0" cellspacing="0" style="border:1px solid #e4e6eb; border-radius:10px; padding:15px; display:inline-block;">
        <tr>
        <td style="font-size:14px; color:#333;">
        <strong>Order ID:</strong> { order.oid }
        </td>
        </tr>
        <tr>
        <td style="font-size:14px; color:#333;">
        <strong>Status:</strong> Cancelled ❌
        </td>
        </tr>
        <tr>
        <td style="font-size:14px; color:#333;">
        <strong>Payment Method:</strong> Online Payment
        </td>
        </tr>
        <tr>
        <td style="font-size:14px; color:#333;">
        <strong>Amount Paid:</strong> ₹{ order.amount }
        </td>
        </tr>
        </table>
        </div>

        <p style="font-size:15px; line-height:1.6;">
        Since this was a prepaid order, your <strong>refund will be processed shortly</strong> to your original payment method. It may take
        <strong>3–7 working days</strong> for the refund to reflect depending on your bank or payment provider.
        </p>

        <p style="font-size:14px; line-height:1.6;">
        You will be notified once the refund has been successfully completed.
        </p>

        <p style="font-size:14px; line-height:1.6;">
        If you did not request this cancellation or have any concerns, please contact our support team immediately and we’ll be happy to help.
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
    
    cod_templates=f"""
        <!DOCTYPE html>

        <html>
        <head>
        <meta charset="UTF-8">
        <title>BuyZone — Order Cancelled</title>
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
        Order Cancellation Confirmation
        </p>
        </td>
        </tr>

        <!-- Body -->

        <tr>
        <td style="padding:30px; color:#333333;">

        <h2 style="margin-top:0;">Hi { order.name },</h2>

        <p style="font-size:15px; line-height:1.6;">
        We want to let you know that your order <strong>#{ order.oid }</strong> has been successfully cancelled.
        </p>

        <!-- Order Info box -->

        <div style="margin:25px 0; text-align:center;">
        <table cellpadding="0" cellspacing="0" style="border:1px solid #e4e6eb; border-radius:10px; padding:15px; display:inline-block;">
        <tr>
        <td style="font-size:14px; color:#333;">
        <strong>Order ID:</strong> { order.oid }
        </td>
        </tr>
        <tr>
        <td style="font-size:14px; color:#333;">
        <strong>Status:</strong> Cancelled ❌
        </td>
        </tr>
        <tr>
        <td style="font-size:14px; color:#333;">
        <strong>Payment Method:</strong> Cash on Delivery
        </td>
        </tr>
        </table>
        </div>

        <p style="font-size:15px; line-height:1.6;">
        Since this order was placed using <strong>Cash on Delivery</strong>, no refund is required and you will not be charged for this order.
        </p>

        <p style="font-size:14px; line-height:1.6;">
        If you did not request this cancellation or need help placing a new order, please reach out to our support team and we’ll be happy to assist you.
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

    if original_amount_paid > 0:
        subject = "Order Cancellation Confirmation — Refund Will Be Processed"
        html_message = prepaid_templates
    else:
        subject = "Order Cancellation Confirmation - No Refund Required"
        html_message = cod_templates

    email = EmailMultiAlternatives(
        subject=subject,
        body="Your order has been cancelled successfully.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email]
    )

    email.attach_alternative(html_message, "text/html")
    import threading
    from helper import send_email_async
    threading.Thread(target=send_email_async, args=(email,)).start()


    messages.success(request, f"Order #{order.oid} cancelled successfully")
    return redirect('profile')


def return_order(request, order_id):

    order = get_object_or_404(
        Orders,
        id=order_id,
        email=request.user.email
    )

    if not order.delivered_at:
        messages.error(request, "This order has not been delivered yet.")
        return redirect('profile')

    if order.is_returned:
        messages.warning(request, "This order is already returned.")
        return redirect('profile')

    # Check 5-day return window
    return_last_date = order.delivered_at + timedelta(days=5)

    if timezone.now() > return_last_date:
        messages.error(request, "Return period has expired (5 days).")
        return redirect('profile')

    # Mark order returned
    order.is_returned = True
    if order.assigned_to:
        pickup_partner = order.assigned_to
    else:
        pickup_partner = None  # still safe

    order.assigned_to = pickup_partner

    OrderUpdate.objects.create(
        order=order,
        update_desc="Return requested — assigned for pickup",
        delivered=False
    )

    order.save()

    messages.success(request, "Return request submitted. Our delivery partner will pick it up soon.")
    return redirect('profile')


def search(request):
    query = request.GET.get("q", "")
    products = Product.objects.none()

    if query:
        products = Product.objects.filter(
            product_name__icontains=query
        ).values("id", "product_name")  # select only needed fields

    return JsonResponse({
        "results": list(products)
    })


import razorpay
from django.conf import settings

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

def refund_payment(payment_id, amount):
    """
    amount must be in paise
    """
    return client.payment.refund(
        payment_id,
        {
            "amount": int(float(amount) * 100),
            "speed": "optimum"
        }
    )

from django.shortcuts import redirect
from django.urls import reverse


class DeliveryBoyRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user = request.user

        # Only logged-in delivery boys
        if user.is_authenticated and user.groups.filter(name="DeliveryBoy").exists():

            delivery_dashboard_url = reverse("delivery_dashboard")

            # Pages jahan redirect nahi karna
            allowed_paths = [
                delivery_dashboard_url,
                reverse("verify_delivery_otp", kwargs={"order_id": 1})[:-2],  # smart match
                reverse("generate_delivery_otp", kwargs={"order_id": 1})[:-2],
                "/logout/",
                "/auth/logout/",
                "/delivery/",
                "/media/",
            ]

            # If user is not already on delivery pages → redirect
            if not any(request.path.startswith(p) for p in allowed_paths):
                return redirect("delivery_dashboard")

        return self.get_response(request)

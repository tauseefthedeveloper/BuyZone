from django.shortcuts import redirect

from django.conf import settings

class AuthUserRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path
        user = request.user

        # 🚨 DO NOT TOUCH MEDIA FILE REQUESTS
        if path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # 🚨 ALSO DON’T TOUCH STATIC FILES
        if path.startswith(settings.STATIC_URL):
            return self.get_response(request)

        # Now your normal logic…
        if user.is_authenticated and (user.is_staff or user.is_superuser):

            if path.startswith("/admin/"):
                return self.get_response(request)

            return redirect("/admin/")

        return self.get_response(request)

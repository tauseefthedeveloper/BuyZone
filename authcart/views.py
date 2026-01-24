from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.core.mail import EmailMessage
from django.conf import settings
from django.views.generic import View
from django.contrib.auth import login,logout,authenticate
from .utils import TokenGenerator,generate_token
# from django.utils.encoding import force_text
from django.utils.encoding import DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.safestring import mark_safe
from django.contrib.auth import authenticate, login
from django.contrib import messages


# Create your views here.
def signup(request):
    if request.method == "POST":
        Name = request.POST['name']
        emails = request.POST['email']
        password = request.POST['pass1']
        confirm_password = request.POST['pass2']

        if password != confirm_password:
            messages.warning(request, "Passwords do not match.")
            return render(request, "signup.html")

        try:
            if User.objects.get(username=emails):
                messages.info(request, "Email already exists.")
                return render(request, 'signup.html')
        except User.DoesNotExist:
            pass

        # Create a new inactive user
        user = User.objects.create_user(username=emails, first_name=Name, email=emails, password=password)
        user.is_active = False
        user.save()

        # Generate activation link
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = generate_token.make_token(user)
        activation_link = f"http://127.0.0.1:8000/auth/activate/{uid}/{token}/"
        # complete_activation_link=mark_safe(f"Activate your account by clicking the link <a target='_blank' href='{activation_link}'>click here!</a>")
        # Show activation link in a success message

         # Email content
        subject = "Activate Your BuyZone Account"
        message = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="UTF-8">
            <title>Activate Your BuyZone Account</title>
            </head>
            <body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">

                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8; padding:20px 0;">
                    <tr>
                    <td align="center">

                        <!-- Main Container -->
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1);">

                        <!-- Header -->
                        <tr>
                            <td style="background-color:#0d6efd; padding:25px; text-align:center;">
                            <h1 style="color:#ffffff; margin:0; font-size:26px;">BuyZone</h1>
                            <p style="color:#e9ecef; margin:5px 0 0; font-size:14px;">
                                Smarter Online Shopping Experience
                            </p>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding:30px; color:#333333;">

                            <h2 style="margin-top:0;">Hi {Name}, 👋</h2>

                            <p style="font-size:15px; line-height:1.6;">
                                Thank you for creating an account on <strong>BuyZone</strong>.
                                You are just one step away from accessing exclusive deals and managing your orders.
                            </p>

                            <p style="font-size:15px; line-height:1.6;">
                                Please click the button below to activate your account:
                            </p>

                            <!-- Button -->
                            <div style="text-align:center; margin:30px 0;">
                                <a href="{activation_link}"
                                style="
                                    background-color:#0d6efd;
                                    color:#ffffff;
                                    padding:14px 28px;
                                    text-decoration:none;
                                    font-size:16px;
                                    font-weight:bold;
                                    border-radius:6px;
                                    display:inline-block;
                                ">
                                Activate My Account
                                </a>
                            </div>

                            <p style="font-size:14px; color:#555;">
                                If the button does not work, copy and paste the following link into your browser:
                            </p>

                            <p style="font-size:13px; word-break:break-all; color:#0d6efd;">
                                {activation_link}
                            </p>

                            <p style="font-size:14px; line-height:1.6; margin-top:20px;">
                                If you did not create this account, you can safely ignore this email.
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
                            © {2025} BuyZone. All rights reserved.
                            </td>
                        </tr>

                        </table>

                    </td>
                    </tr>
                </table>

            </body>
            </html>
        """

        email_message = EmailMessage(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [emails],
        )

        email_message.content_subtype = "html"
        email_message.send(fail_silently=False)

        messages.success(
            request,
            "Account created successfully! Please check your email to activate your account."
        )
        return redirect('auth:signup')

    return render(request, 'signup.html')


class ActivateAccountView(View):
    def get(self,request,uidb64,token):
        try:
            uid=force_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(pk=uid)
        except Exception as identifier:
            user=None
        if user is not None and generate_token.check_token(user,token):
            if user.is_active:
                messages.info(request, "Your account is already activated.")
                return redirect('/auth/login/')
            
            user.is_active=True
            user.save()
            messages.success(request, "Account activated successfully! You can now login.")
            return redirect('/auth/login/')
        
        return render(request, 'activatefail.html')


def handlelogin(request):
    if request.method=="POST":
        username=request.POST['email']
        userpassword=request.POST['pass1']
        myuser=authenticate(username=username,password=userpassword)

        if myuser is not None:
            login(request,myuser)

            messages.success(request,"Login Success!")
            if myuser.groups.filter(name="DeliveryBoy").exists():
                return redirect("delivery_dashboard")
            if request.user.is_staff or request.user.is_superuser:
                return redirect('/admin/')

            return redirect("/")

        messages.error(request,'Invalid Credentials')
        return redirect('/auth/login/')

    return render(request,'login.html')


def handlelogout(request):
    logout(request)
    messages.info(request,"Logout Success!")
    return redirect('/auth/login/')

class RequestResetEmailView(View):
    def get(self,request):
        return render(request,'request-reset-email.html')
    
    def post(self,request):
        email=request.POST['email']
        user=User.objects.filter(email=email)

        if user.exists():
            user = user.first()
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)

            reset_link = f"http://127.0.0.1:8000/auth/set-new-password/{uid}/{token}/"

            message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset="UTF-8">
                <title>Reset Your BuyZone Password</title>
                </head>
                <body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">

                <table width="100%" cellpadding="0" cellspacing="0" style="padding:20px 0;">
                <tr>
                    <td align="center">

                    <!-- Main Card -->
                    <table width="600" cellpadding="0" cellspacing="0"
                        style="background:#ffffff; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.1); overflow:hidden;">

                        <!-- Header -->
                        <tr>
                        <td style="background:#dc3545; padding:25px; text-align:center;">
                            <h1 style="margin:0; color:#ffffff;">BuyZone</h1>
                            <p style="margin:5px 0 0; color:#f8d7da;">Password Reset Request</p>
                        </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                        <td style="padding:30px; color:#333333;">
                            <h2 style="margin-top:0;">Hi {user.first_name}, 👋</h2>

                            <p style="font-size:15px; line-height:1.6;">
                            We received a request to reset your <strong>BuyZone</strong> account password.
                            </p>

                            <p style="font-size:15px;">
                            Click the button below to set a new password:
                            </p>

                            <!-- Button -->
                            <div style="text-align:center; margin:30px 0;">
                            <a href="{reset_link}"
                                style="
                                background:#dc3545;
                                color:#ffffff;
                                padding:14px 28px;
                                text-decoration:none;
                                font-size:16px;
                                font-weight:bold;
                                border-radius:6px;
                                display:inline-block;
                                ">
                                Reset Password
                            </a>
                            </div>

                            <p style="font-size:14px; color:#555;">
                            If the button doesn’t work, copy and paste this link into your browser:
                            </p>

                            <p style="font-size:13px; word-break:break-all; color:#dc3545;">
                            {reset_link}
                            </p>

                            <p style="font-size:14px; margin-top:20px;">
                            If you did not request a password reset, you can safely ignore this email.
                            </p>

                            <p style="margin-top:30px;">
                            Regards,<br>
                            <strong>BuyZone Team</strong>
                            </p>
                        </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                        <td style="background:#f8f9fa; padding:12px; text-align:center; font-size:12px; color:#6c757d;">
                            © 2025 BuyZone. All rights reserved.
                        </td>
                        </tr>

                    </table>

                    </td>
                </tr>
                </table>

                </body>
                </html>
            """


            email_message = EmailMessage(
                subject="Reset Your BuyZone Password",
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[email],
            )
            email_message.content_subtype = "html"  # IMPORTANT
            email_message.send()

            messages.success(
                request,
                "We have sent you an email with instructions to reset your password."
            )
            return redirect('auth:request-reset-email')

        messages.error(request, "No account found with this email.")
        return redirect('auth:request-reset-email')


class SetNewPasswordView(View):

    def get(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token
        }

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.error(request, "Password reset link is invalid or expired.")
                return redirect('auth:request-reset-email')
            messages.success(
                request,
                "User verified. You can now set a new password."
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "Invalid password reset link.")
            return redirect('auth:request-reset-email')

        return render(request, 'set-new-password.html', context)

    def post(self, request, uidb64, token):
        password = request.POST.get('pass1')
        confirm_password = request.POST.get('pass2')

        context = {
            'uidb64': uidb64,
            'token': token
        }

        if not password or not confirm_password:
            messages.warning(request, "Password fields cannot be empty.")
            return render(request, 'set-new-password.html', context)
        
        if password != confirm_password:
            messages.warning(request, "Passwords do not match.")
            return render(request, 'set-new-password.html', context)

        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.error(request, "Password reset link has expired.")
                return redirect('auth:request-reset-email')

            user.set_password(password)
            user.save()

            messages.success(
                request,
                "Password reset successful. Please login with your new password."
            )
            return redirect('auth:handlelogin')

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            messages.error(request, "Something went wrong. Please try again.")
            return redirect('auth:request-reset-email')

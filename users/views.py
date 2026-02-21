from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import Group
import random
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .tokens import account_activation_token
from django.contrib.auth import get_user_model
from .models import CustomUser, PrimarySetting
from .forms import CustomUserCreationForm
from .forms import UserLoginForm

def user_login(request):
    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful!")
            if user.role in [CustomUser.Role.ADMIN, CustomUser.Role.MANAGER]:
                return redirect("/admin/tasks/task/?status__exact=PENDING")
            return redirect("task_list_default")
        else:
            messages.warning(request, "Invalid email or password.")
    else:
        form = UserLoginForm()

    return render(request, "users/signin.html", {"form": form})

def user_logout(request):
    logout(request)
    return redirect("user_login")

def user_registration(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            email = form.cleaned_data.get("username")
            user.email = email
            user.save()
            
            if user.role == CustomUser.Role.MANAGER:
                user.groups.add(Group.objects.get(name="Manager"))
                user.is_staff = True
                user.save()

            primary_setting = PrimarySetting.objects.first()
            if primary_setting and primary_setting.auto_approve:
                user.is_active = True
                user.save()
                login(request, user)
                messages.success(request, "You are now logged in.")
                return redirect("home")
            else:
                messages.success(request, "Your account has been created. Please wait for HR to approve your account.")

    else:
        form = CustomUserCreationForm()

    return render(request, "users/signup.html", {"form": form})

def password_reset(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = CustomUser.objects.get(email=email)
            new_password = generate_password()
            user.set_password(new_password)
            user.save()
            
            # Send password reset email
            current_site = get_current_site(request)
            mail_subject = "Account Password Reset"
            message = render_to_string(
                "users/email_user_password_reset.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "password": new_password,
                    "timestamp": timezone.now(),
                    "login_url": request.build_absolute_uri(reverse("user_login")),    
                },
            )
            to_email = user.email
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            
            messages.success(request, "Login credentials have been sent to your email.")
        except CustomUser.DoesNotExist:
            messages.warning(request, "No user found with this email address.")
    return render(request, "users/password_reset.html")

def generate_password(length=8):
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    password = "".join(random.choice(characters) for _ in range(length))
    return password










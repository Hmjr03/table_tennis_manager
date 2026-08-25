from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from accounts.forms import ActivationResendForm, UserRegistrationForm
from accounts.models import User
from accounts.services import send_account_activation_email


def home(request):
    return render(request, "home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                send_account_activation_email(request, user)

            return redirect("accounts:activation_sent")
    else:
        form = UserRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def activation_sent(request):
    return render(request, "accounts/activation_sent.html")


def activate(request, uidb64, token):
    user = None

    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        pass

    if (
        user is not None
        and default_token_generator.check_token(user, token)
    ):
        user.is_active = True
        user.save(update_fields=["is_active"])
        login(request, user)
        return render(request, "accounts/activation_complete.html")

    return render(
        request,
        "accounts/activation_invalid.html",
        status=400,
    )


def resend_activation(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = ActivationResendForm(request.POST)

        if form.is_valid():
            user = User.objects.filter(
                email__iexact=form.cleaned_data["email"],
                is_active=False,
            ).first()

            if user:
                send_account_activation_email(request, user)

            return redirect("accounts:activation_resent")
    else:
        form = ActivationResendForm()

    return render(
        request,
        "accounts/resend_activation.html",
        {"form": form},
    )


def activation_resent(request):
    return render(request, "accounts/activation_resent.html")


@login_required
def dashboard(request):
    return redirect("dashboard:home")

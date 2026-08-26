from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone
from django.conf import settings

from accounts.data_portability import export_user_data
from accounts.forms import (
    AccountDeletionForm,
    AccountDeletionRequestForm,
    ActivationResendForm,
    EmailDeletionConfirmationForm,
    UserRegistrationForm,
)
from accounts.models import User
from accounts.services import (
    send_account_activation_email,
    send_account_deletion_email,
)


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
                accepted_at = timezone.now()
                user.terms_accepted_at = accepted_at
                user.privacy_notice_acknowledged_at = accepted_at
                user.legal_documents_version = (
                    settings.LEGAL_DOCUMENTS_VERSION
                )
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
def privacy_center(request):
    return render(request, "accounts/privacy_center.html")


@login_required
@require_POST
@never_cache
def export_account_data(request):
    response = JsonResponse(
        export_user_data(request.user),
        json_dumps_params={"indent": 2, "ensure_ascii": False},
    )
    response["Content-Disposition"] = (
        'attachment; filename="table-tennis-manager-data.json"'
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def delete_account(request):
    if request.method == "POST":
        form = AccountDeletionForm(request.user, request.POST)

        if form.is_valid():
            user = request.user
            with transaction.atomic():
                user.delete()
            logout(request)
            return render(
                request,
                "accounts/account_deleted.html",
            )
    else:
        form = AccountDeletionForm(request.user)

    return render(
        request,
        "accounts/delete_account.html",
        {"form": form},
    )


def request_account_deletion(request):
    if request.user.is_authenticated:
        return redirect("accounts:delete_account")

    if request.method == "POST":
        form = AccountDeletionRequestForm(request.POST)

        if form.is_valid():
            user = User.objects.filter(
                email__iexact=form.cleaned_data["email"]
            ).first()

            if user:
                send_account_deletion_email(request, user)

            return redirect("accounts:deletion_requested")
    else:
        form = AccountDeletionRequestForm()

    return render(
        request,
        "accounts/request_account_deletion.html",
        {"form": form},
    )


def deletion_requested(request):
    return render(request, "accounts/deletion_requested.html")


def delete_via_email(request, uidb64, token):
    user = None

    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        pass

    token_is_valid = (
        user is not None
        and default_token_generator.check_token(user, token)
    )

    if not token_is_valid:
        return render(
            request,
            "accounts/deletion_link_invalid.html",
            status=400,
        )

    if request.method == "POST":
        form = EmailDeletionConfirmationForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user.delete()
            if request.user.is_authenticated:
                logout(request)
            return render(request, "accounts/account_deleted.html")
    else:
        form = EmailDeletionConfirmationForm()

    return render(
        request,
        "accounts/delete_via_email.html",
        {"form": form, "account_email": user.email},
    )


@login_required
def dashboard(request):
    return redirect("dashboard:home")

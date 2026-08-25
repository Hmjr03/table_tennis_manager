from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label=_("Email"),
    )
    accept_terms = forms.BooleanField(
        required=True,
        label=_("I have read and accept the Terms of Use."),
    )
    acknowledge_privacy = forms.BooleanField(
        required=True,
        label=_("I have read and acknowledge the Privacy Policy."),
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "role",
        ]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                _("An account with this email already exists.")
            )

        return email


class ActivationResendForm(forms.Form):
    email = forms.EmailField(
        required=True,
        label=_("Email"),
    )


class AccountDeletionForm(forms.Form):
    current_password = forms.CharField(
        label=_("Current password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password"}
        ),
    )
    confirm_deletion = forms.BooleanField(
        label=_("I understand that this action is permanent."),
        required=True,
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_current_password(self):
        password = self.cleaned_data["current_password"]

        if not self.user.check_password(password):
            raise forms.ValidationError(
                _("The password entered is incorrect.")
            )

        return password


class AccountDeletionRequestForm(forms.Form):
    email = forms.EmailField(
        required=True,
        label=_("Email"),
    )


class EmailDeletionConfirmationForm(forms.Form):
    confirm_deletion = forms.BooleanField(
        label=_("I understand that this action is permanent."),
        required=True,
    )

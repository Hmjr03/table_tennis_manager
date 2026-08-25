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

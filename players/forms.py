from django import forms

from players.models import Player


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = (
            "first_name",
            "last_name",
            "date_of_birth",
            "hand",
        )
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "First name",
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Last name",
                    "autocomplete": "family-name",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "hand": forms.Select(),
        }

    def clean_first_name(self):
        first_name = self.cleaned_data["first_name"].strip()

        if len(first_name) < 2:
            raise forms.ValidationError(
                "First name must contain at least 2 characters."
            )

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data["last_name"].strip()

        if len(last_name) < 2:
            raise forms.ValidationError(
                "Last name must contain at least 2 characters."
            )

        return last_name


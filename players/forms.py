from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from players.models import Player


class PlayerForm(forms.ModelForm):
    world_ranking = forms.IntegerField(
        required=False,
        min_value=0,
        initial=0,
        label=_("World ranking"),
        widget=forms.NumberInput(attrs={"min": 0, "placeholder": "e.g. 125"}),
    )
    national_ranking = forms.IntegerField(
        required=False,
        min_value=0,
        initial=0,
        label=_("National ranking"),
        widget=forms.NumberInput(attrs={"min": 0, "placeholder": "e.g. 18"}),
    )
    date_of_birth = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date", "autocomplete": "bday"},
        ),
    )

    class Meta:
        model = Player
        fields = (
            "first_name",
            "last_name",
            "date_of_birth",
            "hand",
            "world_ranking",
            "national_ranking",
        )
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": _("First name"),
                    "autocomplete": "given-name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": _("Last name"),
                    "autocomplete": "family-name",
                }
            ),
            "hand": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date_of_birth"].widget.attrs["max"] = (
            timezone.localdate().isoformat()
        )

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get("date_of_birth")
        if date_of_birth and date_of_birth > timezone.localdate():
            raise forms.ValidationError(
                _("Date of birth cannot be in the future.")
            )
        return date_of_birth

    def clean_world_ranking(self):
        return self.cleaned_data.get("world_ranking") or 0

    def clean_national_ranking(self):
        return self.cleaned_data.get("national_ranking") or 0

    def clean_first_name(self):
        first_name = self.cleaned_data["first_name"].strip()

        if len(first_name) < 2:
            raise forms.ValidationError(
                _("First name must contain at least 2 characters.")
            )

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data["last_name"].strip()

        if len(last_name) < 2:
            raise forms.ValidationError(
                _("Last name must contain at least 2 characters.")
            )

        return last_name

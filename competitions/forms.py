from django import forms
from django.utils.translation import gettext_lazy as _

from competitions.models import Competition
from players.models import Player


class CompetitionForm(forms.ModelForm):
    start_date = forms.DateField(
        label=_("Start date"),
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label=_("End date"),
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
    )

    class Meta:
        model = Competition
        fields = (
            "name",
            "competition_type",
            "status",
            "start_date",
            "end_date",
            "location",
            "season",
            "players",
            "notes",
        )
        labels = {
            "name": _("Competition name"),
            "competition_type": _("Competition type"),
            "status": _("Status"),
            "start_date": _("Start date"),
            "end_date": _("End date"),
            "location": _("Location"),
            "season": _("Season"),
            "players": _("Participating athletes"),
            "notes": _("Notes"),
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": _("Official competition name")}
            ),
            "location": forms.TextInput(
                attrs={"placeholder": _("City, venue or sports hall")}
            ),
            "season": forms.TextInput(
                attrs={"placeholder": _("Example: 2026/27")}
            ),
            "players": forms.CheckboxSelectMultiple(),
            "notes": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": _("Objectives, registration details and important information"),
                }
            ),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.fields["players"].queryset = (
            Player.objects.filter(user=owner)
            if owner is not None
            else Player.objects.none()
        )

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 3:
            raise forms.ValidationError(
                _("Competition name must contain at least 3 characters.")
            )
        return name

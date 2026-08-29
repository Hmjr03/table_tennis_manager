from django import forms
from django.utils.translation import gettext_lazy as _

from finances.models import Transaction


class TransactionForm(forms.ModelForm):
    date = forms.DateField(
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    class Meta:
        model = Transaction
        fields = (
            "transaction_type",
            "area",
            "category",
            "competition_record",
            "amount",
            "date",
            "description",
            "payment_method",
            "status",
            "is_recurring",
            "notes",
        )
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "description": forms.TextInput(attrs={"placeholder": _("What was this transaction for?")}),
            "notes": forms.Textarea(attrs={"rows": 4, "placeholder": _("Optional details")}),
        }
        labels = {
            "transaction_type": _("Type"), "area": _("Area"),
            "category": _("Category"), "amount": _("Amount"),
            "competition_record": _("Registered competition"),
            "date": _("Date"), "description": _("Description"),
            "payment_method": _("Payment method"), "status": _("Status"),
            "is_recurring": _("Recurring transaction"), "notes": _("Notes"),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        choice_prompts = {
            "transaction_type": _("Select transaction type"),
            "area": _("Select area"),
            "category": _("Select category"),
        }
        for field_name, prompt in choice_prompts.items():
            field = self.fields[field_name]
            field.choices = [
                ("", prompt),
                *(choice for choice in field.choices if choice[0]),
            ]

        self.fields["competition_record"].empty_label = _(
            "No linked competition"
        )
        if owner is not None:
            self.fields["competition_record"].queryset = (
                owner.competitions.all().order_by("start_date", "name")
            )
        else:
            self.fields["competition_record"].queryset = (
                self.fields["competition_record"].queryset.none()
            )

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 3:
            raise forms.ValidationError(
                _("Description must contain at least 3 characters.")
            )
        return description

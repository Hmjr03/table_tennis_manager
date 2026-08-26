from django import forms
from django.utils.translation import gettext_lazy as _

from planning.models import CalendarEvent


DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class CalendarEventForm(forms.ModelForm):
    start_datetime = forms.DateTimeField(
        input_formats=[
            DATETIME_LOCAL_FORMAT,
            "%Y-%m-%d %H:%M",
        ],
        widget=forms.DateTimeInput(
            format=DATETIME_LOCAL_FORMAT,
            attrs={
                "type": "datetime-local",
                "step": 60,
            },
        ),
    )

    end_datetime = forms.DateTimeField(
        input_formats=[
            DATETIME_LOCAL_FORMAT,
            "%Y-%m-%d %H:%M",
        ],
        widget=forms.DateTimeInput(
            format=DATETIME_LOCAL_FORMAT,
            attrs={
                "type": "datetime-local",
                "step": 60,
            },
        ),
    )

    class Meta:
        model = CalendarEvent
        fields = (
            "title",
            "description",
            "event_type",
            "competition_record",
            "start_datetime",
            "end_datetime",
            "location",
            "priority",
        )

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": _("Event title"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": _("Describe this event..."),
                    "rows": 5,
                }
            ),
            "event_type": forms.Select(),
            "location": forms.TextInput(
                attrs={
                    "placeholder": _("Location"),
                }
            ),
            "priority": forms.Select(),
        }
        labels = {
            "title": _("Event title"), "description": _("Description"),
            "event_type": _("Event type"), "start_datetime": _("Start date and time"),
            "competition_record": _("Registered competition"),
            "end_datetime": _("End date and time"), "location": _("Location"),
            "priority": _("Priority"),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner is not None:
            self.fields["competition_record"].queryset = (
                owner.competitions.all().order_by("start_date", "name")
            )
        else:
            self.fields["competition_record"].queryset = (
                self.fields["competition_record"].queryset.none()
            )

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if len(title) < 3:
            raise forms.ValidationError(
                _("Event title must contain at least 3 characters.")
            )

        return title

    def clean(self):
        cleaned_data = super().clean()

        start_datetime = cleaned_data.get("start_datetime")
        end_datetime = cleaned_data.get("end_datetime")

        if (
            start_datetime
            and end_datetime
            and end_datetime <= start_datetime
        ):
            raise forms.ValidationError(
                _("The end date and time must be after the start date and time.")
            )

        return cleaned_data


class EventScheduleForm(forms.ModelForm):
    start_datetime = forms.DateTimeField(
        label=_("Start date and time"),
        input_formats=[DATETIME_LOCAL_FORMAT, "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            format=DATETIME_LOCAL_FORMAT,
            attrs={"type": "datetime-local", "step": 60},
        ),
    )
    end_datetime = forms.DateTimeField(
        label=_("End date and time"),
        input_formats=[DATETIME_LOCAL_FORMAT, "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            format=DATETIME_LOCAL_FORMAT,
            attrs={"type": "datetime-local", "step": 60},
        ),
    )

    class Meta:
        model = CalendarEvent
        fields = ("start_datetime", "end_datetime", "location")
        labels = {"location": _("Location")}
        widgets = {
            "location": forms.TextInput(attrs={"placeholder": _("Location")}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get("start_datetime")
        end_datetime = cleaned_data.get("end_datetime")
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            raise forms.ValidationError(
                _("The end date and time must be after the start date and time.")
            )
        return cleaned_data


class EventClassificationForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ("event_type", "priority", "competition_record")
        labels = {
            "event_type": _("Event type"),
            "priority": _("Priority"),
            "competition_record": _("Registered competition"),
        }

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        if owner is not None:
            self.fields["competition_record"].queryset = owner.competitions.all()
        else:
            self.fields["competition_record"].queryset = (
                self.fields["competition_record"].queryset.none()
            )


class EventDescriptionForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ("description",)
        labels = {"description": _("Description")}
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 6, "placeholder": _("Describe this event...")}
            ),
        }

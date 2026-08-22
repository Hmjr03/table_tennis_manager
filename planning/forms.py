from django import forms

from planning.models import CalendarEvent


class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = (
            "title",
            "description",
            "event_type",
            "start_datetime",
            "end_datetime",
            "location",
            "priority",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Event title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Describe this event...",
                    "rows": 5,
                }
            ),
            "event_type": forms.Select(),
            "start_datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "placeholder": "Location",
                }
            ),
            "priority": forms.Select(),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if len(title) < 3:
            raise forms.ValidationError(
                "Event title must contain at least 3 characters."
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
                "The end date and time must be after "
                "the start date and time."
            )

        return cleaned_data

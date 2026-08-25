from django import forms
from django.utils.translation import gettext_lazy as _

from notes.models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = (
            "title",
            "category",
            "competition_record",
            "content",
            "is_pinned",
        )
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": _("A clear note title")}),
            "content": forms.Textarea(
                attrs={
                    "rows": 10,
                    "placeholder": _("Write decisions, ideas, reminders or observations..."),
                }
            ),
        }
        labels = {
            "title": _("Title"), "category": _("Category"),
            "content": _("Content"), "is_pinned": _("Pinned"),
            "competition_record": _("Registered competition"),
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
                _("Note title must contain at least 3 characters.")
            )
        return title

    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if not content:
            raise forms.ValidationError(_("Note content cannot be empty."))
        return content

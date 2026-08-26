from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Note(models.Model):
    class Category(models.TextChoices):
        GENERAL = "GENERAL", _("General")
        TRAINING = "TRAINING", _("Training")
        COMPETITION = "COMPETITION", _("Competition")
        TACTICS = "TACTICS", _("Tactics")
        FINANCE = "FINANCE", _("Finance")
        PERSONAL = "PERSONAL", _("Personal")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    competition_record = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_notes",
    )
    title = models.CharField(max_length=160)
    content = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-updated_at"]

    def __str__(self):
        return self.title

    def clean(self):
        if (
            self.competition_record_id
            and self.owner_id
            and self.competition_record.owner_id != self.owner_id
        ):
            raise ValidationError(
                {
                    "competition_record": _(
                        "The selected competition does not belong to this account."
                    )
                }
            )

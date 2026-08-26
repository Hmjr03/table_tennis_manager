from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class CalendarEvent(models.Model):
    class EventType(models.TextChoices):
        TRAINING = "TRAINING", _("Training")
        COMPETITION = "COMPETITION", _("Competition")
        TRAVEL = "TRAVEL", _("Travel")
        RECOVERY = "RECOVERY", _("Recovery")
        EVALUATION = "EVALUATION", _("Evaluation")
        MEETING = "MEETING", _("Meeting")
        PERSONAL = "PERSONAL", _("Personal")
        OTHER = "OTHER", _("Other")

    class Priority(models.TextChoices):
        LOW = "LOW", _("Low")
        MEDIUM = "MEDIUM", _("Medium")
        HIGH = "HIGH", _("High")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calendar_events",
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.OTHER,
    )

    start_datetime = models.DateTimeField()

    end_datetime = models.DateTimeField()

    location = models.CharField(
        max_length=255,
        blank=True,
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    competition_record = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )

    is_competition_sync = models.BooleanField(
        default=False,
        editable=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["start_datetime"]
        constraints = [
            models.UniqueConstraint(
                fields=["competition_record"],
                condition=Q(is_competition_sync=True),
                name="unique_synced_event_per_competition",
            )
        ]

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

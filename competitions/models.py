from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Competition(models.Model):
    class CompetitionType(models.TextChoices):
        LEAGUE = "LEAGUE", _("League")
        TOURNAMENT = "TOURNAMENT", _("Tournament")
        CHAMPIONSHIP = "CHAMPIONSHIP", _("Championship")
        CUP = "CUP", _("Cup")
        OTHER = "OTHER", _("Other")

    class Status(models.TextChoices):
        PLANNED = "PLANNED", _("Planned")
        ACTIVE = "ACTIVE", _("In progress")
        COMPLETED = "COMPLETED", _("Completed")
        CANCELLED = "CANCELLED", _("Cancelled")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="competitions",
    )
    name = models.CharField(max_length=200)
    competition_type = models.CharField(
        max_length=20,
        choices=CompetitionType.choices,
        default=CompetitionType.TOURNAMENT,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    season = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    players = models.ManyToManyField(
        "players.Player",
        blank=True,
        related_name="competitions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date", "name"]
        indexes = [
            models.Index(fields=["owner", "start_date"]),
            models.Index(fields=["owner", "status"]),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}
        if self.end_date and self.end_date < self.start_date:
            errors["end_date"] = _(
                "The end date cannot be earlier than the start date."
            )
        if errors:
            raise ValidationError(errors)

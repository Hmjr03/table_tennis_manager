from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Match(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", _("Scheduled")
        COMPLETED = "COMPLETED", _("Completed")
        CANCELLED = "CANCELLED", _("Cancelled")

    class BestOf(models.IntegerChoices):
        THREE = 3, _("Best of 3")
        FIVE = 5, _("Best of 5")
        SEVEN = 7, _("Best of 7")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matches",
    )

    player = models.ForeignKey(
        "players.Player",
        on_delete=models.CASCADE,
        related_name="matches_as_player",
    )

    opponent_name = models.CharField(
        max_length=150,
    )

    competition = models.CharField(
        max_length=200,
        blank=True,
    )

    competition_record = models.ForeignKey(
        "competitions.Competition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches",
    )

    played_at = models.DateTimeField()

    best_of = models.PositiveSmallIntegerField(
        choices=BestOf.choices,
        default=BestOf.FIVE,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    player_sets_won = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    opponent_sets_won = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-played_at", "-created_at"]
        indexes = [
            models.Index(
                fields=["owner", "-played_at"],
            ),
            models.Index(
                fields=["owner", "status"],
            ),
            models.Index(
                fields=["player", "-played_at"],
            ),
        ]

    def __str__(self):
        return (
            f"{self.player} vs {self.opponent_name}"
            f" - {self.played_at:%Y-%m-%d}"
        )

    def clean(self):
        errors = {}

        if self.player_id and self.owner_id:
            if self.player.user_id != self.owner_id:
                errors["player"] = (
                    _("The selected player does not belong to this account.")
                )

        if self.competition_record_id and self.owner_id:
            if self.competition_record.owner_id != self.owner_id:
                errors["competition_record"] = _(
                    "The selected competition does not belong to this account."
                )

        if self.status == self.Status.COMPLETED:
            if (
                self.player_sets_won is None
                or self.opponent_sets_won is None
            ):
                errors["player_sets_won"] = (
                    _("Both scores are required for a completed match.")
                )
            else:
                target = self.best_of // 2 + 1

                player_won = (
                    self.player_sets_won == target
                    and self.opponent_sets_won < target
                )

                opponent_won = (
                    self.opponent_sets_won == target
                    and self.player_sets_won < target
                )

                if not player_won and not opponent_won:
                    errors["player_sets_won"] = _(
                        "For Best of %(best_of)s, the winner must have "
                        "exactly %(target)s sets."
                    ) % {"best_of": self.best_of, "target": target}

        else:
            if (
                self.player_sets_won is not None
                or self.opponent_sets_won is not None
            ):
                errors["player_sets_won"] = (
                    _("Scores can only be recorded for completed matches.")
                )

        if errors:
            raise ValidationError(errors)

    @property
    def result(self):
        if self.status == self.Status.SCHEDULED:
            return "Scheduled"

        if self.status == self.Status.CANCELLED:
            return "Cancelled"

        if (
            self.player_sets_won is None
            or self.opponent_sets_won is None
        ):
            return "Pending"

        if self.player_sets_won > self.opponent_sets_won:
            return "Win"

        return "Loss"

    @property
    def score(self):
        if (
            self.player_sets_won is None
            or self.opponent_sets_won is None
        ):
            return "—"

        return (
            f"{self.player_sets_won}"
            f" - "
            f"{self.opponent_sets_won}"
        )

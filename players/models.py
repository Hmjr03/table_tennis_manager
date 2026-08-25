from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Player(models.Model):
    class Hand(models.TextChoices):
        RIGHT = "RIGHT", _("Right-handed")
        LEFT = "LEFT", _("Left-handed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="players",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(
        null=True,
        blank=True,
    )
    hand = models.CharField(
        max_length=10,
        choices=Hand.choices,
        default=Hand.RIGHT,
    )
    national_ranking = models.PositiveIntegerField(
        default=0,
        verbose_name=_("National ranking"),
    )
    world_ranking = models.PositiveIntegerField(
        default=0,
        verbose_name=_("World ranking"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

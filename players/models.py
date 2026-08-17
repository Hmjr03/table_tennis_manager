from django.conf import settings
from django.db import models


class Player(models.Model):
    class Hand(models.TextChoices):
        RIGHT = "RIGHT", "Right-handed"
        LEFT = "LEFT", "Left-handed"

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
    ranking = models.PositiveIntegerField(
        default=0,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        "email address",
        unique=True,
    )

    class Role(models.TextChoices):
        ATHLETE = "ATHLETE", "Athlete"
        COACH = "COACH", "Coach"
        CLUB = "CLUB", "Club"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATHLETE,
    )

    def __str__(self):
        return self.username

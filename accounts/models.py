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

    terms_accepted_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    privacy_notice_acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    legal_documents_version = models.CharField(
        max_length=20,
        blank=True,
    )
    onboarding_dismissed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.username

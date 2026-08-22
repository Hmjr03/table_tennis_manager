from django.conf import settings
from django.db import models


class CalendarEvent(models.Model):
    class EventType(models.TextChoices):
        TRAINING = "TRAINING", "Training"
        COMPETITION = "COMPETITION", "Competition"
        TRAVEL = "TRAVEL", "Travel"
        RECOVERY = "RECOVERY", "Recovery"
        EVALUATION = "EVALUATION", "Evaluation"
        MEETING = "MEETING", "Meeting"
        PERSONAL = "PERSONAL", "Personal"
        OTHER = "OTHER", "Other"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["start_datetime"]

    def __str__(self):
        return self.title

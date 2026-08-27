from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Subscription(models.Model):
    class Plan(models.TextChoices):
        STARTER = "STARTER", _("Starter")
        PROFESSIONAL = "PROFESSIONAL", _("Professional")
        ORGANIZATION = "ORGANIZATION", _("Organization")

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        TRIALING = "TRIALING", _("Trial")
        PAST_DUE = "PAST_DUE", _("Payment pending")
        CANCELED = "CANCELED", _("Canceled")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.CharField(
        max_length=20,
        choices=Plan.choices,
        default=Plan.STARTER,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user__username",)

    def __str__(self):
        return f"{self.user} — {self.get_plan_display()}"

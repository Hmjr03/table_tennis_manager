from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Subscription(models.Model):
    class Plan(models.TextChoices):
        STARTER = "STARTER", _("Starter")
        PROFESSIONAL = "PROFESSIONAL", _("Professional")
        ORGANIZATION = "ORGANIZATION", _("Organization")

    class Status(models.TextChoices):
        INCOMPLETE = "INCOMPLETE", _("Incomplete")
        ACTIVE = "ACTIVE", _("Active")
        TRIALING = "TRIALING", _("Trial")
        PAST_DUE = "PAST_DUE", _("Payment pending")
        UNPAID = "UNPAID", _("Unpaid")
        PAUSED = "PAUSED", _("Paused")
        CANCELED = "CANCELED", _("Canceled")

    class BillingInterval(models.TextChoices):
        MONTHLY = "MONTHLY", _("Monthly")
        YEARLY = "YEARLY", _("Yearly")

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
    billing_interval = models.CharField(
        max_length=10,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )
    stripe_price_id = models.CharField(max_length=255, blank=True, default="")
    cancel_at_period_end = models.BooleanField(default=False)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_ends_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user__username",)

    def __str__(self):
        return f"{self.user} — {self.get_plan_display()}"

    @property
    def is_trial_active(self):
        return (
            self.status == self.Status.TRIALING
            and self.trial_ends_at is not None
            and self.trial_ends_at > timezone.now()
        )

    @property
    def trial_days_remaining(self):
        if not self.is_trial_active:
            return 0
        seconds = (self.trial_ends_at - timezone.now()).total_seconds()
        return max(1, int((seconds + 86399) // 86400))

    @property
    def has_product_access(self):
        if self.status == self.Status.ACTIVE:
            return True
        return self.is_trial_active


class StripeWebhookEvent(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", _("Received")
        PROCESSED = "PROCESSED", _("Processed")
        FAILED = "FAILED", _("Failed")
        IGNORED = "IGNORED", _("Ignored")

    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.event_type} — {self.event_id}"

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from subscriptions.models import Subscription


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_starter_subscription(sender, instance, created, **kwargs):
    if created:
        defaults = {}
        if settings.SUBSCRIPTION_TRIAL_ENABLED:
            defaults = {
                "plan": Subscription.Plan.PROFESSIONAL,
                "status": Subscription.Status.TRIALING,
                "trial_ends_at": timezone.now()
                + timedelta(days=settings.SUBSCRIPTION_TRIAL_DAYS),
            }
        Subscription.objects.get_or_create(user=instance, defaults=defaults)

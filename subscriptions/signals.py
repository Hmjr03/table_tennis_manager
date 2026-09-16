from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from subscriptions.models import Subscription
from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from hashlib import sha256
from subscriptions.models import ClosedTestInvitation


@receiver(user_logged_in)
def grant_authorized_closed_test_access(sender, user, **kwargs):
    if not user.is_active:
        return
    digest = sha256(user.email.strip().lower().encode()).hexdigest()
    with transaction.atomic():
        now = timezone.now()
        claimed = ClosedTestInvitation.objects.filter(
            email_digest=digest, redeemed_at__isnull=True,
        ).update(redeemed_at=now)
        if not claimed:
            return
        subscription, _ = Subscription.objects.get_or_create(user=user)
        until = now + timedelta(days=30)
        if not subscription.closed_test_ends_at or subscription.closed_test_ends_at < until:
            subscription.closed_test_ends_at = until
            subscription.save(update_fields=["closed_test_ends_at", "updated_at"])


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_starter_subscription(sender, instance, created, **kwargs):
    if created:
        defaults = {}
        if settings.SUBSCRIPTION_TRIAL_ENABLED:
            defaults = {
                "plan": Subscription.Plan.STARTER,
                "status": Subscription.Status.TRIALING,
                "trial_ends_at": timezone.now()
                + timedelta(days=settings.SUBSCRIPTION_TRIAL_DAYS),
            }
        Subscription.objects.get_or_create(user=instance, defaults=defaults)

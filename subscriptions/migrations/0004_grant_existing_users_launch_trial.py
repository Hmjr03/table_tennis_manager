from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def grant_launch_trial(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    trial_ends_at = timezone.now() + timedelta(days=7)
    Subscription.objects.exclude(stripe_mode="LIVE").update(
        plan="PROFESSIONAL",
        status="TRIALING",
        trial_ends_at=trial_ends_at,
        current_period_ends_at=None,
        canceled_at=None,
        cancel_at_period_end=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0003_subscription_stripe_mode"),
    ]

    operations = [
        migrations.RunPython(grant_launch_trial, migrations.RunPython.noop),
    ]

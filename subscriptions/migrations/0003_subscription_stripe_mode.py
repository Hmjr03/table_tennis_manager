from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0002_stripewebhookevent_subscription_billing_interval_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="stripe_mode",
            field=models.CharField(
                blank=True,
                choices=[("TEST", "Test"), ("LIVE", "Production")],
                default="",
                max_length=10,
            ),
        ),
    ]

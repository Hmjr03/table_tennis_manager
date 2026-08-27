from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_existing_subscriptions(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    Subscription = apps.get_model("subscriptions", "Subscription")
    Subscription.objects.bulk_create(
        [Subscription(user_id=user_id) for user_id in User.objects.values_list("id", flat=True)],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("plan", models.CharField(choices=[("STARTER", "Starter"), ("PROFESSIONAL", "Professional"), ("ORGANIZATION", "Organization")], default="STARTER", max_length=20)),
                ("status", models.CharField(choices=[("ACTIVE", "Active"), ("TRIALING", "Trial"), ("PAST_DUE", "Payment pending"), ("CANCELED", "Canceled")], default="ACTIVE", max_length=20)),
                ("trial_ends_at", models.DateTimeField(blank=True, null=True)),
                ("current_period_ends_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="subscription", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("user__username",)},
        ),
        migrations.RunPython(
            create_existing_subscriptions,
            migrations.RunPython.noop,
        ),
    ]

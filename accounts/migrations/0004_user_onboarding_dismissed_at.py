from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_legal_acceptance"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="onboarding_dismissed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

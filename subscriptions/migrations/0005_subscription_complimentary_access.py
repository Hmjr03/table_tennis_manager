from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0004_grant_existing_users_launch_trial")]
    operations = [migrations.AddField(
        model_name="subscription", name="complimentary_access",
        field=models.BooleanField(
            "Acesso de cortesia", default=False,
            help_text="Acesso sem cobrança e sem vencimento, revogável pela administração.",
        ),
    )]

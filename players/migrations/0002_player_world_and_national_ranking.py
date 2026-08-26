from django.db import migrations, models
import django.utils.translation


class Migration(migrations.Migration):
    dependencies = [
        ("players", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="player",
            old_name="ranking",
            new_name="national_ranking",
        ),
        migrations.AlterField(
            model_name="player",
            name="national_ranking",
            field=models.PositiveIntegerField(
                default=0,
                verbose_name=django.utils.translation.gettext_lazy(
                    "National ranking"
                ),
            ),
        ),
        migrations.AddField(
            model_name="player",
            name="world_ranking",
            field=models.PositiveIntegerField(
                default=0,
                verbose_name=django.utils.translation.gettext_lazy(
                    "World ranking"
                ),
            ),
        ),
    ]

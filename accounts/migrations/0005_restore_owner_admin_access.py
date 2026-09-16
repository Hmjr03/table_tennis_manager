from django.db import migrations


def restore_owner_admin_access(apps, schema_editor):
    """Owner-authorized recovery for the existing Hmjr account only.

    Do not create an account, change a password, or reactivate a disabled user.
    Missing accounts in development and test databases are intentionally ignored.
    """
    User = apps.get_model("accounts", "User")
    User.objects.using(schema_editor.connection.alias).filter(
        username="Hmjr", is_active=True
    ).update(is_staff=True, is_superuser=True)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_user_onboarding_dismissed_at")]

    # Automatic rollback must not remove privileges that predated this recovery.
    # Any later revocation is an explicit administrative action.
    operations = [migrations.RunPython(restore_owner_admin_access, migrations.RunPython.noop)]

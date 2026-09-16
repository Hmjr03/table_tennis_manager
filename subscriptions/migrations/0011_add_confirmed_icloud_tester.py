from django.db import migrations


def add_invitation(apps, schema_editor):
    Invitation = apps.get_model("subscriptions", "ClosedTestInvitation")
    Invitation.objects.using(schema_editor.connection.alias).get_or_create(
        email_digest="448c0beee8d090f4982c79052275accafc1183f597347c7bc04e3d6f7e0eaa39",
    )


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0010_add_two_closed_test_invitations")]
    operations = [migrations.RunPython(add_invitation, migrations.RunPython.noop)]

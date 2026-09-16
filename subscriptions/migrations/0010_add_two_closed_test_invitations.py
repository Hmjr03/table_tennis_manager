from django.db import migrations

EMAIL_DIGESTS = ('5d9bb83fa353746a9293aa94f243c6c3eba94a530592533fc5c2833e1fcc53de', 'ebc15b3b62eb954ed4465c0c49b9e3476d5ad1ca09642d3432c868b54af90b8b')

def add_invitations(apps, schema_editor):
    Invitation = apps.get_model("subscriptions", "ClosedTestInvitation")
    for digest in EMAIL_DIGESTS:
        Invitation.objects.using(schema_editor.connection.alias).get_or_create(email_digest=digest)

class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0009_add_six_closed_test_invitations")]
    operations = [migrations.RunPython(add_invitations, migrations.RunPython.noop)]

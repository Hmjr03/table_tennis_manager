from django.db import migrations

EMAIL_DIGESTS = ('0c1f8c2a6afbacb6266f649f8cd33ec9e96b2ee55a91ada9ce000370d780cdcb', '3c4aa0c0ac325a50b4efc1cfa6fb27cac48f93bfa302d463a1fbeb8697042a5e', '4f5a59ef9860f29b19a98534d4081a4af549ef54031314965ee0d4cbe632476c', '69f7af73bdd196d9d2c5dc6a90570dde1c72cf012eede95fedcbae8fe35b3124', '7c24f898be6d737b95ca8e377a148a1d20b9c19f1ec4afb70d7e9e3334b172e8', 'ed3555b154ffee01e6bf20656420c6f2f7de8355e43848e714a652bc8e9468ac')

def add_invitations(apps, schema_editor):
    Invitation = apps.get_model("subscriptions", "ClosedTestInvitation")
    for digest in EMAIL_DIGESTS:
        Invitation.objects.using(schema_editor.connection.alias).get_or_create(email_digest=digest)

class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0008_authorized_closed_test_group")]
    operations = [migrations.RunPython(add_invitations, migrations.RunPython.noop)]

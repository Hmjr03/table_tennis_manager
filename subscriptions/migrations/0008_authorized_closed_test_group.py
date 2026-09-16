from django.db import migrations


# Authorized group of 12; no raw contact addresses in source control.
EMAIL_DIGESTS = ('14ca8a1a9375f1d60513c053e6b922e12bc9e37779890febd92b83dd5e9ccab2', '160aa0d53a60e7dcca50e9796c897df08f835157f4a6a2e60a0c3b4fee417970', '247b8ef77dadffe34b4cf79e5acbd5d398c740b93e43529704fd331bc3cc3120', '62df197d14ee1d1b420cc829672d1db4ef454d3ab43067c76de1694cc3260146', '660a59dc1df78a55c5600b3db6cfecfba76d127768694ba48d0c2ae124dc5837', '6671b39d53dd4058e99d0645e511412ee38712b0d5f893a6b09455550f1b1c6d', '728ea9bf6b1e7e2ffa549c36bae777a77b5823fe182b792b7c7a760e62a7fbea', '90076f5b69e28f7c55bb1dacb2a460fdb959178bd667db26451d8f2ce9b87204', 'bfa4ed191073c13d504d7caaaa34686b27d62d9887381a20485c9146c9db6084', 'da27061c70ae8837bc343715116ed79e8b3a26fc8a6e2c443a44266bdba54532', 'dd41aa1fb54dd2cedcda9b412ae57e5f895670833d53d6b7dbb9ada0f5caabc5', 'ebf53056cf116f6b5afb7b5dd8a2a51ed62a2c9150a52a9fa344b127bfa6a787')


def seed_invitations(apps, schema_editor):
    Invitation = apps.get_model("subscriptions", "ClosedTestInvitation")
    for digest in EMAIL_DIGESTS:
        Invitation.objects.using(schema_editor.connection.alias).get_or_create(email_digest=digest)


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0007_closed_test_invitations")]
    operations = [migrations.RunPython(seed_invitations, migrations.RunPython.noop)]

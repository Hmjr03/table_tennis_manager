from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def prepare_review_account(apps, schema_editor):
    alias = schema_editor.connection.alias
    User = apps.get_model("accounts", "User")
    user = User.objects.using(alias).filter(
        username="google-play-review", email="google-play-review@example.invalid",
        is_active=True, is_staff=False, is_superuser=False,
    ).first()
    if user is None:
        return
    Subscription = apps.get_model("subscriptions", "Subscription")
    subscription = Subscription.objects.using(alias).filter(user_id=user.pk).first()
    if subscription is None or subscription.stripe_customer_id or subscription.stripe_subscription_id:
        raise RuntimeError("Review account requires an existing subscription without billing links.")
    subscription.complimentary_access = True
    subscription.plan = "ORGANIZATION"
    subscription.status = "ACTIVE"
    subscription.trial_ends_at = None
    subscription.save(using=alias, update_fields=[
        "complimentary_access", "plan", "status", "trial_ends_at", "updated_at",
    ])
    now = timezone.now().replace(minute=0, second=0, microsecond=0)
    Player = apps.get_model("players", "Player")
    player, _ = Player.objects.using(alias).get_or_create(
        user_id=user.pk, first_name="Alex", last_name="Demo",
        defaults={"hand": "RIGHT"},
    )
    Match = apps.get_model("matches", "Match")
    Match.objects.using(alias).get_or_create(
        owner_id=user.pk, player_id=player.pk, opponent_name="Jordan Demo",
        competition="Demo match — fictional data",
        defaults={"played_at": now - timedelta(days=1), "best_of": 5,
                  "status": "COMPLETED", "player_sets_won": 3,
                  "opponent_sets_won": 1, "notes": "Fictional example for app review."},
    )
    Event = apps.get_model("planning", "CalendarEvent")
    Event.objects.using(alias).get_or_create(
        owner_id=user.pk, title="Demo training — fictional data",
        defaults={"description": "Fictional example for app review.",
                  "event_type": "TRAINING", "start_datetime": now + timedelta(days=1),
                  "end_datetime": now + timedelta(days=1, hours=1), "priority": "MEDIUM"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0005_subscription_complimentary_access"),
        ("accounts", "0005_restore_owner_admin_access"),
        ("players", "0002_player_world_and_national_ranking"),
        ("matches", "0002_match_competition_record"),
        ("planning", "0003_calendarevent_is_competition_sync_and_more"),
    ]
    # Keep reviewer-created data on rollback; revocation is an admin action.
    operations = [migrations.RunPython(prepare_review_account, migrations.RunPython.noop)]

from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings

from players.models import Player
from matches.models import Match
from planning.models import CalendarEvent


@override_settings(SUBSCRIPTION_ACCESS_ENFORCED=True, STRIPE_LIVE_MODE=True)
class ReviewAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.reviewer = User.objects.create_user(
            username="google-play-review", email="google-play-review@example.invalid",
        )
        self.owner = User.objects.create_user(username="owner", email="owner@example.invalid")

    def prepare(self):
        import_module(
            "subscriptions.migrations.0006_prepare_authorized_review_account"
        ).prepare_review_account(apps, SimpleNamespace(connection=connection))

    def test_access_is_scoped_revocable_and_does_not_grant_admin(self):
        password_before = self.reviewer.password
        owner_before = self.owner.subscription.__dict__.copy()
        self.prepare()
        self.prepare()
        self.reviewer.refresh_from_db()
        self.owner.subscription.refresh_from_db()
        subscription = self.reviewer.subscription
        self.assertTrue(subscription.has_product_access)
        self.assertFalse(subscription.has_paid_access)
        self.assertIsNone(subscription.trial_ends_at)
        self.assertFalse(subscription.stripe_customer_id)
        self.assertFalse(subscription.stripe_subscription_id)
        self.assertFalse(self.reviewer.is_staff)
        self.assertFalse(self.reviewer.is_superuser)
        self.assertEqual(self.reviewer.password, password_before)
        for field in ("plan", "status", "complimentary_access", "trial_ends_at"):
            self.assertEqual(getattr(self.owner.subscription, field), owner_before[field])
        self.assertEqual(Player.objects.filter(user=self.reviewer).count(), 1)
        self.assertEqual(Match.objects.filter(owner=self.reviewer).count(), 1)
        self.assertEqual(CalendarEvent.objects.filter(owner=self.reviewer).count(), 1)
        self.assertFalse(Player.objects.filter(user=self.owner).exists())
        self.client.force_login(self.reviewer)
        for path in ("/dashboard/", "/players/", "/matches/", "/competitions/",
                     "/planning/calendar/", "/finances/", "/notes/"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertEqual(self.client.get("/admin/").status_code, 302)
        subscription.complimentary_access = False
        subscription.save()
        self.assertRedirects(self.client.get("/dashboard/"), "/plans/")

    def test_wrong_identity_is_not_granted_access(self):
        self.reviewer.email = "different@example.invalid"
        self.reviewer.save()
        self.prepare()
        self.assertFalse(self.reviewer.subscription.complimentary_access)
        self.assertFalse(Player.objects.filter(user=self.reviewer).exists())

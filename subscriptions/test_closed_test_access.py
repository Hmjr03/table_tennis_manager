from datetime import timedelta
from hashlib import sha256
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from players.views import _player_limit_for
from subscriptions.models import ClosedTestInvitation, Subscription
from subscriptions.signals import grant_authorized_closed_test_access


@override_settings(SUBSCRIPTION_TRIAL_ENABLED=True, SUBSCRIPTION_TRIAL_DAYS=7,
                   SUBSCRIPTION_ACCESS_ENFORCED=True)
class ClosedTestAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", email="Tester@example.invalid", is_active=False,
        )
        self.invite = ClosedTestInvitation.objects.create(
            email_digest=sha256(b"tester@example.invalid").hexdigest(),
        )

    def grant(self):
        grant_authorized_closed_test_access(None, self.user)
        return Subscription.objects.get(user=self.user)

    def test_activation_and_first_login_start_30_days_without_admin_or_billing(self):
        self.grant()
        self.invite.refresh_from_db()
        self.assertIsNone(self.invite.redeemed_at)
        self.user.is_active = True
        self.user.save()
        now = timezone.now()
        with patch("subscriptions.signals.timezone.now", return_value=now):
            sub = self.grant()
        self.assertEqual(sub.closed_test_ends_at, now + timedelta(days=30))
        self.assertTrue(sub.has_product_access)
        self.assertFalse(sub.stripe_subscription_id)
        self.assertFalse(self.user.is_staff or self.user.is_superuser)
        self.assertEqual(_player_limit_for(self.user), 300)
        with patch("subscriptions.signals.timezone.now", return_value=now + timedelta(days=10)):
            repeated = self.grant()
        self.assertEqual(repeated.closed_test_ends_at, sub.closed_test_ends_at)
        with patch("subscriptions.models.timezone.now", return_value=now + timedelta(days=31)):
            self.assertFalse(sub.has_closed_test_access)
            self.assertFalse(sub.has_product_access)

    def test_paid_subscription_and_other_clients_are_preserved(self):
        self.user.is_active = True
        self.user.save()
        sub = self.user.subscription
        sub.plan = Subscription.Plan.PROFESSIONAL
        sub.status = Subscription.Status.ACTIVE
        sub.stripe_mode = Subscription.StripeMode.TEST
        sub.stripe_subscription_id = "sub_test_existing"
        sub.save()
        updated = self.grant()
        for field in ("plan", "status", "stripe_mode", "stripe_subscription_id", "trial_ends_at"):
            self.assertEqual(getattr(updated, field), getattr(sub, field))
        other = get_user_model().objects.create_user(username="other", email="other@example.invalid")
        original_end = other.subscription.trial_ends_at
        grant_authorized_closed_test_access(None, other)
        other.subscription.refresh_from_db()
        self.assertIsNone(other.subscription.closed_test_ends_at)
        self.assertEqual(other.subscription.trial_ends_at, original_end)

    def test_account_recreation_does_not_restart_redeemed_invitation(self):
        self.user.is_active = True
        self.user.save()
        self.grant()
        self.user.delete()
        self.user = get_user_model().objects.create_user(username="replacement", email="tester@example.invalid")
        self.assertIsNone(self.grant().closed_test_ends_at)

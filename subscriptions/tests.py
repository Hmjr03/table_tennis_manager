from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.test import override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock, patch

from subscriptions.models import Subscription


User = get_user_model()


class SubscriptionFoundationTests(TestCase):
    def test_new_user_receives_starter_subscription(self):
        user = User.objects.create_user(
            username="starter-user",
            email="starter@example.com",
            password="SecurePass123!",
        )

        self.assertEqual(user.subscription.plan, Subscription.Plan.STARTER)
        self.assertEqual(user.subscription.status, Subscription.Status.ACTIVE)

    def test_deleting_user_deletes_only_its_subscription(self):
        first_user = User.objects.create_user(
            username="first-user",
            email="first@example.com",
            password="SecurePass123!",
        )
        second_user = User.objects.create_user(
            username="second-user",
            email="second@example.com",
            password="SecurePass123!",
        )
        first_subscription_id = first_user.subscription.pk

        first_user.delete()

        self.assertFalse(
            Subscription.objects.filter(pk=first_subscription_id).exists()
        )
        self.assertTrue(
            Subscription.objects.filter(user=second_user).exists()
        )

    def test_plans_page_is_public_and_has_no_checkout(self):
        response = self.client.get(reverse("subscriptions:plans"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Commercial preview")
        self.assertNotContains(response, "checkout")
        self.assertNotContains(response, "card number")

    def test_authenticated_user_sees_current_plan(self):
        user = User.objects.create_user(
            username="current-user",
            email="current@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("subscriptions:plans"))

        self.assertContains(response, "Current plan")
        self.assertContains(response, "Active on your account")
        self.assertEqual(Subscription.objects.filter(user=user).count(), 1)

    def test_plans_page_is_translated_to_portuguese_and_spanish(self):
        expectations = (
            ("pt-br", "Um plano para cada etapa da sua jornada"),
            ("es", "Un plan para cada etapa de tu recorrido"),
        )

        for language, expected_text in expectations:
            with self.subTest(language=language):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = language
                response = self.client.get(reverse("subscriptions:plans"))
                self.assertContains(response, expected_text)


class BillingSafetyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="billing-user",
            email="billing@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(self.user)

    def test_checkout_is_blocked_by_default(self):
        response = self.client.post(
            reverse("subscriptions:create_checkout"),
            {"plan": "PROFESSIONAL", "interval": "MONTHLY"},
        )
        self.assertRedirects(response, reverse("subscriptions:plans"))

    def test_portal_is_blocked_by_default(self):
        response = self.client.post(reverse("subscriptions:billing_portal"))
        self.assertRedirects(response, reverse("subscriptions:plans"))

    def test_webhook_is_unavailable_by_default(self):
        response = self.client.post(
            reverse("subscriptions:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)

    @override_settings(STRIPE_BILLING_ENABLED=True)
    @patch("subscriptions.views.create_checkout_session")
    def test_enabled_checkout_redirects_to_provider(self, create_session):
        create_session.return_value = Mock(url="https://billing.example/session")
        response = self.client.post(
            reverse("subscriptions:create_checkout"),
            {"plan": "PROFESSIONAL", "interval": "MONTHLY"},
        )
        self.assertRedirects(
            response,
            "https://billing.example/session",
            fetch_redirect_response=False,
        )

    @override_settings(STRIPE_BILLING_ENABLED=True)
    @patch("subscriptions.views.create_billing_portal_session")
    def test_enabled_portal_redirects_to_provider(self, create_session):
        create_session.return_value = Mock(url="https://billing.example/portal")
        response = self.client.post(reverse("subscriptions:billing_portal"))
        self.assertRedirects(
            response,
            "https://billing.example/portal",
            fetch_redirect_response=False,
        )


class ProfessionalTrialTests(TestCase):
    @override_settings(
        SUBSCRIPTION_TRIAL_ENABLED=True,
        SUBSCRIPTION_TRIAL_DAYS=7,
    )
    def test_new_user_receives_seven_day_professional_trial(self):
        before = timezone.now() + timedelta(days=7)
        user = User.objects.create_user(
            username="trial-user",
            email="trial@example.com",
            password="SecurePass123!",
        )
        after = timezone.now() + timedelta(days=7)

        self.assertEqual(user.subscription.plan, Subscription.Plan.PROFESSIONAL)
        self.assertEqual(user.subscription.status, Subscription.Status.TRIALING)
        self.assertGreaterEqual(user.subscription.trial_ends_at, before)
        self.assertLessEqual(user.subscription.trial_ends_at, after)
        self.assertTrue(user.subscription.has_product_access)

    @override_settings(
        SUBSCRIPTION_TRIAL_ENABLED=True,
        SUBSCRIPTION_TRIAL_DAYS=7,
    )
    def test_trial_banner_shows_remaining_days(self):
        user = User.objects.create_user(
            username="banner-user",
            email="banner@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, "Professional trial")
        self.assertContains(response, "7 days remaining")

    @override_settings(SUBSCRIPTION_ACCESS_ENFORCED=True)
    def test_expired_trial_is_redirected_to_plans(self):
        user = User.objects.create_user(
            username="expired-user",
            email="expired@example.com",
            password="SecurePass123!",
        )
        subscription = user.subscription
        subscription.plan = Subscription.Plan.PROFESSIONAL
        subscription.status = Subscription.Status.TRIALING
        subscription.trial_ends_at = timezone.now() - timedelta(seconds=1)
        subscription.save()
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertRedirects(response, reverse("subscriptions:plans"))

        plans_response = self.client.get(reverse("subscriptions:plans"))
        self.assertNotContains(plans_response, "Active on your account")

    @override_settings(SUBSCRIPTION_ACCESS_ENFORCED=True)
    def test_existing_active_account_remains_available(self):
        user = User.objects.create_user(
            username="existing-user",
            email="existing@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)

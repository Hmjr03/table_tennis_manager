from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.test import override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock, patch

from subscriptions.models import Subscription
from subscriptions.services import (
    BillingConfigurationError,
    create_billing_portal_session,
    create_checkout_session,
)


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

    def test_starter_user_does_not_see_inactive_plan_as_current(self):
        user = User.objects.create_user(
            username="current-user",
            email="current@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("subscriptions:plans"))

        self.assertNotContains(response, "Current plan")
        self.assertNotContains(response, "Active on your account")
        self.assertEqual(Subscription.objects.filter(user=user).count(), 1)

    def test_checkout_return_messages_do_not_claim_unconfirmed_activation(self):
        success_response = self.client.get(
            reverse("subscriptions:plans"),
            {"payment": "success"},
        )
        canceled_response = self.client.get(
            reverse("subscriptions:plans"),
            {"payment": "canceled"},
        )

        self.assertContains(success_response, "as soon as payment is confirmed")
        self.assertContains(canceled_response, "No charge was made")

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

    def test_checkout_cycle_uses_the_branded_accessible_control(self):
        user = User.objects.create_user(
            username="plan-control-user",
            email="plan-control@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(user)

        with self.settings(STRIPE_BILLING_ENABLED=True):
            response = self.client.get(reverse("subscriptions:plans"))

        self.assertContains(response, 'class="billing-cycle-field"')
        self.assertContains(response, 'class="billing-cycle-select"')
        self.assertContains(response, 'name="interval" aria-label="Billing cycle"')

    @override_settings(STRIPE_BILLING_ENABLED=True)
    def test_android_app_shows_plans_without_external_checkout(self):
        user = User.objects.create_user(
            username="android-plan-user",
            email="android-plan@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("subscriptions:plans"),
            {"platform": "android"},
        )

        self.assertContains(response, "Subscriptions are managed")
        self.assertContains(response, "Available with an active subscription")
        self.assertNotContains(response, 'class="plan-checkout-form"')
        self.assertNotContains(response, 'action="/plans/start/"')

        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "pt-br"
        portuguese_response = self.client.get(
            reverse("subscriptions:plans"),
            {"platform": "android"},
        )
        self.assertContains(
            portuguese_response,
            "As assinaturas são administradas no site do ETM Manager",
        )


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
    @patch("subscriptions.views.create_checkout_session")
    def test_android_checkout_request_cannot_open_stripe(self, create_session):
        response = self.client.post(
            reverse("subscriptions:create_checkout"),
            {
                "plan": "PROFESSIONAL",
                "interval": "MONTHLY",
                "platform": "android",
            },
        )

        self.assertRedirects(
            response,
            reverse("subscriptions:plans") + "?platform=android",
        )
        create_session.assert_not_called()

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
    def test_new_user_receives_seven_day_individual_trial(self):
        before = timezone.now() + timedelta(days=7)
        user = User.objects.create_user(
            username="trial-user",
            email="trial@example.com",
            password="SecurePass123!",
        )
        after = timezone.now() + timedelta(days=7)

        self.assertEqual(user.subscription.plan, Subscription.Plan.STARTER)
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

        self.assertContains(response, "Individual trial")
        self.assertContains(response, "7 days remaining")

    @override_settings(
        STRIPE_BILLING_ENABLED=True,
        SUBSCRIPTION_TRIAL_ENABLED=True,
        SUBSCRIPTION_TRIAL_DAYS=7,
    )
    def test_trial_user_can_choose_monthly_or_yearly_for_all_available_plans(self):
        user = User.objects.create_user(
            username="trial-checkout-user",
            email="trial-checkout@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("subscriptions:plans"))

        self.assertContains(response, 'value="MONTHLY"', count=3)
        self.assertContains(response, 'value="YEARLY"', count=3)
        self.assertContains(response, 'value="PROFESSIONAL"', count=1)
        self.assertContains(response, 'value="ORGANIZATION"', count=1)
        self.assertContains(response, 'value="STARTER"', count=1)

    @override_settings(
        STRIPE_BILLING_ENABLED=True,
        STRIPE_LIVE_MODE=True,
    )
    def test_test_customer_does_not_show_live_billing_portal(self):
        user = User.objects.create_user(
            username="test-portal-user",
            email="test-portal@example.com",
            password="SecurePass123!",
        )
        subscription = user.subscription
        subscription.stripe_customer_id = "cus_test_customer"
        subscription.stripe_mode = Subscription.StripeMode.TEST
        subscription.save()
        self.client.force_login(user)

        response = self.client.get(reverse("subscriptions:plans"))

        self.assertNotContains(response, reverse("subscriptions:billing_portal"))

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
        self.assertContains(plans_response, "Your free trial has ended")
        self.assertContains(plans_response, "keeping your saved data")
        self.assertTrue(subscription.is_trial_expired)

    @override_settings(SUBSCRIPTION_ACCESS_ENFORCED=True)
    def test_starter_account_without_trial_is_redirected_to_plans(self):
        user = User.objects.create_user(
            username="existing-user",
            email="existing@example.com",
            password="SecurePass123!",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertRedirects(response, reverse("subscriptions:plans"))

    @override_settings(SUBSCRIPTION_ACCESS_ENFORCED=True)
    def test_staff_account_keeps_administrative_access(self):
        user = User.objects.create_user(
            username="staff-user",
            email="staff@example.com",
            password="SecurePass123!",
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)


class StripeEnvironmentIsolationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mode-user",
            email="mode@example.com",
            password="SecurePass123!",
        )

    @override_settings(
        STRIPE_BILLING_ENABLED=True,
        STRIPE_LIVE_MODE=True,
        STRIPE_SECRET_KEY="sk_live_example",
        STRIPE_PRICE_PROFESSIONAL_MONTHLY="price_live_monthly",
    )
    @patch("subscriptions.services._stripe")
    def test_live_checkout_does_not_reuse_test_customer(self, stripe_mock):
        subscription = self.user.subscription
        subscription.stripe_customer_id = "cus_test_customer"
        subscription.stripe_mode = Subscription.StripeMode.TEST
        subscription.save()
        stripe_mock.return_value.checkout.Session.create.return_value = Mock(
            url="https://billing.example/session"
        )

        create_checkout_session(
            user=self.user,
            plan=Subscription.Plan.PROFESSIONAL,
            interval=Subscription.BillingInterval.MONTHLY,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

        parameters = stripe_mock.return_value.checkout.Session.create.call_args.kwargs
        self.assertNotIn("customer", parameters)
        self.assertEqual(parameters["customer_email"], self.user.email)
        self.assertEqual(parameters["metadata"]["stripe_mode"], "LIVE")

    @override_settings(
        STRIPE_BILLING_ENABLED=True,
        STRIPE_LIVE_MODE=True,
        STRIPE_SECRET_KEY="sk_live_example",
    )
    def test_live_portal_rejects_test_customer(self):
        subscription = self.user.subscription
        subscription.stripe_customer_id = "cus_test_customer"
        subscription.stripe_mode = Subscription.StripeMode.TEST
        subscription.save()

        with self.assertRaises(BillingConfigurationError):
            create_billing_portal_session(
                user=self.user,
                return_url="https://example.com/plans",
            )

    @override_settings(STRIPE_LIVE_MODE=True)
    def test_test_subscription_does_not_grant_live_access(self):
        subscription = self.user.subscription
        subscription.plan = Subscription.Plan.PROFESSIONAL
        subscription.status = Subscription.Status.ACTIVE
        subscription.stripe_mode = Subscription.StripeMode.TEST
        subscription.save()

        self.assertFalse(subscription.has_product_access)

    @override_settings(STRIPE_LIVE_MODE=True)
    def test_live_subscription_grants_live_access(self):
        subscription = self.user.subscription
        subscription.plan = Subscription.Plan.PROFESSIONAL
        subscription.status = Subscription.Status.ACTIVE
        subscription.stripe_mode = Subscription.StripeMode.LIVE
        subscription.save()

        self.assertTrue(subscription.has_product_access)

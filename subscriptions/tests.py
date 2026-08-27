from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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

import re

from django.core import mail
from django.conf import settings
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from accounts.models import User


class HomePageTests(TestCase):
    def test_home_page_is_available(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_accounts_login_page_is_available(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)


class RegistrationTests(TestCase):
    def test_user_can_register_and_is_logged_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "maria-athlete",
                "email": "MARIA@example.com",
                "first_name": "Maria",
                "last_name": "Silva",
                "role": User.Role.ATHLETE,
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )

        self.assertRedirects(response, reverse("dashboard:home"))

        user = User.objects.get(username="maria-athlete")
        self.assertEqual(user.email, "maria@example.com")
        self.assertEqual(user.role, User.Role.ATHLETE)
        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(user.pk),
        )

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing-user",
            email="existing@example.com",
            password="SecurePass123!",
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new-user",
                "email": "EXISTING@example.com",
                "first_name": "New",
                "last_name": "User",
                "role": User.Role.COACH,
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _("An account with this email already exists."),
        )
        self.assertEqual(User.objects.count(), 1)

    def test_authenticated_user_cannot_open_registration(self):
        user = User.objects.create_user(
            username="coach",
            email="coach@example.com",
            password="SecurePass123!",
            role=User.Role.COACH,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:register"))

        self.assertRedirects(response, reverse("dashboard:home"))


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="club-manager",
            email="club@example.com",
            password="SecurePass123!",
            role=User.Role.CLUB,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))

        expected_url = (
            f"{reverse('accounts:login')}?next="
            f"{reverse('accounts:dashboard')}"
        )
        self.assertRedirects(response, expected_url)

    def test_user_can_log_in_and_reach_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.username,
                "password": "SecurePass123!",
            },
        )

        self.assertRedirects(response, reverse("dashboard:home"))

        response = self.client.get(reverse("dashboard:home"))
        self.assertContains(response, "club-manager")

    def test_legacy_account_dashboard_redirects_to_current_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertRedirects(response, reverse("dashboard:home"))

    def test_user_can_log_out(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
)
class PasswordRecoveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="maria-athlete",
            email="maria@example.com",
            password="OriginalPass123!",
        )

    def test_login_page_links_to_password_recovery(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertContains(
            response,
            reverse("accounts:password_reset"),
        )

    def test_recovery_page_is_translated(self):
        expected_text = {
            "pt-br": "Recupere sua senha",
            "es": "Recupera tu contraseña",
        }

        for language, heading in expected_text.items():
            with self.subTest(language=language):
                self.client.cookies[
                    settings.LANGUAGE_COOKIE_NAME
                ] = language
                response = self.client.get(
                    reverse("accounts:password_reset")
                )
                self.assertContains(response, heading)

    def test_password_recovery_sends_email_for_active_user(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "MARIA@example.com"},
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_done"),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["maria@example.com"])
        self.assertIn("/accounts/reset/", mail.outbox[0].body)

    def test_unknown_email_uses_same_confirmation_without_sending(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "unknown@example.com"},
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_done"),
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_user_can_set_new_password_from_recovery_link(self):
        self.client.post(
            reverse("accounts:password_reset"),
            {"email": self.user.email},
        )
        reset_path = re.search(
            r"https?://[^/]+(/accounts/reset/[^\s]+)",
            mail.outbox[0].body,
        ).group(1)

        response = self.client.get(reset_path)
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            response.url,
            {
                "new_password1": "NewSecurePass456!",
                "new_password2": "NewSecurePass456!",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_complete"),
        )
        self.user.refresh_from_db()
        self.assertTrue(
            self.user.check_password("NewSecurePass456!")
        )

import re

from django.core import mail
from django.conf import settings
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from accounts.models import User
from competitions.models import Competition
from finances.models import Transaction
from matches.models import Match
from notes.models import Note
from planning.models import CalendarEvent
from players.models import Player

from datetime import timedelta
from decimal import Decimal
from django.utils import timezone


class HomePageTests(TestCase):
    def test_home_page_is_available(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_accounts_login_page_is_available(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)


class RegistrationTests(TestCase):
    @override_settings(
        EMAIL_BACKEND=(
            "django.core.mail.backends.locmem.EmailBackend"
        ),
    )
    def test_user_can_register_and_receives_verification_email(self):
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
                "accept_terms": "on",
                "acknowledge_privacy": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:activation_sent"),
        )

        user = User.objects.get(username="maria-athlete")
        self.assertEqual(user.email, "maria@example.com")
        self.assertEqual(user.role, User.Role.ATHLETE)
        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.terms_accepted_at)
        self.assertIsNotNone(
            user.privacy_notice_acknowledged_at
        )
        self.assertEqual(
            user.legal_documents_version,
            settings.LEGAL_DOCUMENTS_VERSION,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/activate/", mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        html_email = mail.outbox[0].alternatives[0]
        self.assertEqual(html_email.mimetype, "text/html")
        self.assertIn("/accounts/activate/", html_email.content)

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
                "accept_terms": "on",
                "acknowledge_privacy": "on",
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

    def test_registration_requires_both_legal_acknowledgements(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "no-legal-acceptance",
                "email": "no-legal@example.com",
                "role": User.Role.ATHLETE,
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "accept_terms",
            "This field is required.",
        )
        self.assertFormError(
            response.context["form"],
            "acknowledge_privacy",
            "This field is required.",
        )
        self.assertFalse(
            User.objects.filter(
                username="no-legal-acceptance"
            ).exists()
        )


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


class AccountCenterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="account-owner",
            email="owner@example.com",
            first_name="Account",
            last_name="Owner",
            password="OriginalPass123!",
            role=User.Role.COACH,
        )
        self.other_user = User.objects.create_user(
            username="other-owner",
            email="other-owner@example.com",
            password="OriginalPass123!",
        )

    def test_account_center_requires_authentication(self):
        response = self.client.get(reverse("accounts:account_center"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:account_center')}",
        )

    def test_account_center_shows_identity_plan_and_own_capacity(self):
        Player.objects.create(
            user=self.user,
            first_name="Visible",
            last_name="Athlete",
        )
        Player.objects.create(
            user=self.other_user,
            first_name="Private",
            last_name="Athlete",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:account_center"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account Owner")
        self.assertContains(response, "owner@example.com")
        self.assertContains(response, "Starter")
        self.assertEqual(response.context["players_used"], 1)
        self.assertNotContains(response, "Private Athlete")
        self.assertNotContains(response, "card number")
        self.assertNotContains(response, "checkout")

    def test_authenticated_user_can_change_password_and_stays_logged_in(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": "OriginalPass123!",
                "new_password1": "UpdatedPass456!",
                "new_password2": "UpdatedPass456!",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("accounts:password_change_done"))
        self.assertContains(response, "Password updated")
        self.assertIn("_auth_user_id", self.client.session)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("UpdatedPass456!"))

    def test_account_center_is_available_in_portuguese_and_spanish(self):
        self.client.force_login(self.user)
        expectations = (
            ("pt-br", "Minha conta", "Treinador"),
            ("es", "Mi cuenta", "Entrenador"),
        )

        for language, title, role in expectations:
            with self.subTest(language=language):
                response = self.client.post(
                    reverse("set_language"),
                    {
                        "language": language,
                        "next": reverse("accounts:account_center"),
                    },
                    follow=True,
                )
                self.assertContains(response, title)
                self.assertContains(response, role)


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
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        html_email = mail.outbox[0].alternatives[0]
        self.assertEqual(html_email.mimetype, "text/html")
        self.assertIn("/accounts/reset/", html_email.content)

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


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    ),
)
class EmailVerificationTests(TestCase):
    def registration_data(self):
        return {
            "username": "new-athlete",
            "email": "new@example.com",
            "role": User.Role.ATHLETE,
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
            "accept_terms": "on",
            "acknowledge_privacy": "on",
        }

    def register_user(self):
        self.client.post(
            reverse("accounts:register"),
            self.registration_data(),
        )
        return User.objects.get(username="new-athlete")

    def test_valid_link_activates_and_logs_user_in(self):
        user = self.register_user()
        activation_path = re.search(
            r"https?://[^/]+(/accounts/activate/[^\s]+)",
            mail.outbox[0].body,
        ).group(1)

        response = self.client.get(activation_path)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/activation_complete.html",
        )
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(
            str(self.client.session["_auth_user_id"]),
            str(user.pk),
        )

    def test_activation_link_can_be_used_only_once(self):
        self.register_user()
        activation_path = re.search(
            r"https?://[^/]+(/accounts/activate/[^\s]+)",
            mail.outbox[0].body,
        ).group(1)

        self.client.get(activation_path)
        response = self.client.get(activation_path)

        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(
            response,
            "accounts/activation_invalid.html",
        )

    def test_inactive_user_can_request_new_activation_link(self):
        user = User.objects.create_user(
            username="pending-athlete",
            email="pending@example.com",
            password="SecurePass123!",
            is_active=False,
        )

        response = self.client.post(
            reverse("accounts:resend_activation"),
            {"email": "PENDING@example.com"},
        )

        self.assertRedirects(
            response,
            reverse("accounts:activation_resent"),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])

    def test_resend_does_not_reveal_unknown_or_active_email(self):
        User.objects.create_user(
            username="active-athlete",
            email="active@example.com",
            password="SecurePass123!",
        )

        for email in ("active@example.com", "unknown@example.com"):
            with self.subTest(email=email):
                response = self.client.post(
                    reverse("accounts:resend_activation"),
                    {"email": email},
                )
                self.assertRedirects(
                    response,
                    reverse("accounts:activation_resent"),
                )

        self.assertEqual(len(mail.outbox), 0)

    def test_verification_page_is_translated(self):
        expected_text = {
            "pt-br": "Verifique seu e-mail",
            "es": "Verifica tu correo",
        }

        for language, heading in expected_text.items():
            with self.subTest(language=language):
                self.client.cookies[
                    settings.LANGUAGE_COOKIE_NAME
                ] = language
                response = self.client.get(
                    reverse("accounts:activation_sent")
                )
                self.assertContains(response, heading)


class AccountDataExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="data-owner",
            email="owner@example.com",
            password="SecurePass123!",
        )
        self.other_user = User.objects.create_user(
            username="other-owner",
            email="other@example.com",
            password="SecurePass123!",
        )
        self.player = Player.objects.create(
            user=self.user,
            first_name="Maria",
            last_name="Silva",
        )
        Player.objects.create(
            user=self.other_user,
            first_name="Private",
            last_name="Player",
        )
        self.competition = Competition.objects.create(
            owner=self.user,
            name="National Cup",
            start_date=timezone.localdate(),
        )
        Match.objects.create(
            owner=self.user,
            player=self.player,
            opponent_name="Ana",
            played_at=timezone.now(),
        )
        CalendarEvent.objects.create(
            owner=self.user,
            title="Training",
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=1),
        )
        Transaction.objects.create(
            owner=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PROFESSIONAL,
            category=Transaction.Category.TRAINING,
            amount=Decimal("25.50"),
            date=timezone.localdate(),
            description="Training fee",
        )
        Note.objects.create(
            owner=self.user,
            title="Strategy",
            content="Serve short",
        )

    def test_export_requires_authentication_and_post(self):
        url = reverse("accounts:export_account_data")

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_export_contains_complete_owned_data_only(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:export_account_data")
        )
        payload = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertEqual(payload["account"]["email"], self.user.email)
        self.assertNotIn("password", payload["account"])
        self.assertEqual(len(payload["players"]), 1)
        self.assertEqual(payload["players"][0]["first_name"], "Maria")
        self.assertEqual(len(payload["competitions"]), 1)
        self.assertEqual(len(payload["matches"]), 1)
        self.assertEqual(len(payload["calendar_events"]), 1)
        self.assertEqual(payload["transactions"][0]["amount"], "25.50")
        self.assertEqual(payload["notes"][0]["title"], "Strategy")


class AccountDeletionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="delete-me",
            email="delete@example.com",
            password="SecurePass123!",
        )
        self.player = Player.objects.create(
            user=self.user,
            first_name="Delete",
            last_name="Me",
        )
        self.competition = Competition.objects.create(
            owner=self.user,
            name="Delete Cup",
            start_date=timezone.localdate(),
        )
        self.match = Match.objects.create(
            owner=self.user,
            player=self.player,
            opponent_name="Delete Opponent",
            played_at=timezone.now(),
        )
        self.event = CalendarEvent.objects.create(
            owner=self.user,
            title="Delete Event",
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timedelta(hours=1),
        )
        self.transaction = Transaction.objects.create(
            owner=self.user,
            transaction_type=Transaction.TransactionType.EXPENSE,
            area=Transaction.Area.PERSONAL,
            category=Transaction.Category.OTHER,
            amount=Decimal("10.00"),
            date=timezone.localdate(),
            description="Delete transaction",
        )
        Note.objects.create(
            owner=self.user,
            title="Private note",
            content="Delete this",
        )
        self.client.force_login(self.user)

    def test_wrong_password_does_not_delete_account(self):
        response = self.client.post(
            reverse("accounts:delete_account"),
            {
                "current_password": "WrongPassword!",
                "confirm_deletion": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertContains(response, "The password entered is incorrect.")

    def test_confirmed_deletion_removes_account_and_related_data(self):
        response = self.client.post(
            reverse("accounts:delete_account"),
            {
                "current_password": "SecurePass123!",
                "confirm_deletion": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/account_deleted.html")
        self.assertFalse(User.objects.filter(username="delete-me").exists())
        self.assertFalse(Player.objects.filter(pk=self.player.pk).exists())
        self.assertFalse(
            Competition.objects.filter(pk=self.competition.pk).exists()
        )
        self.assertFalse(Match.objects.filter(pk=self.match.pk).exists())
        self.assertFalse(
            CalendarEvent.objects.filter(pk=self.event.pk).exists()
        )
        self.assertFalse(
            Transaction.objects.filter(pk=self.transaction.pk).exists()
        )
        self.assertFalse(Note.objects.filter(title="Private note").exists())
        self.assertNotIn("_auth_user_id", self.client.session)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class ExternalAccountDeletionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="external-delete",
            email="external@example.com",
            password="SecurePass123!",
        )

    def test_public_request_sends_generic_response_and_secure_link(self):
        response = self.client.post(
            reverse("accounts:request_account_deletion"),
            {"email": "EXTERNAL@example.com"},
        )

        self.assertRedirects(
            response,
            reverse("accounts:deletion_requested"),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/delete-confirm/", mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)
        html_email = mail.outbox[0].alternatives[0]
        self.assertEqual(html_email.mimetype, "text/html")
        self.assertIn("/accounts/delete-confirm/", html_email.content)

    def test_unknown_email_uses_same_response_without_email(self):
        response = self.client.post(
            reverse("accounts:request_account_deletion"),
            {"email": "unknown@example.com"},
        )

        self.assertRedirects(
            response,
            reverse("accounts:deletion_requested"),
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_email_link_can_permanently_delete_account(self):
        self.client.post(
            reverse("accounts:request_account_deletion"),
            {"email": self.user.email},
        )
        deletion_path = re.search(
            r"https?://[^/]+(/accounts/delete-confirm/[^\s]+)",
            mail.outbox[0].body,
        ).group(1)

        response = self.client.post(
            deletion_path,
            {"confirm_deletion": "on"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/account_deleted.html")
        self.assertFalse(
            User.objects.filter(username="external-delete").exists()
        )

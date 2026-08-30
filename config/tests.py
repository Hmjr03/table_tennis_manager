from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import struct

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import OperationalError
from django.test import TestCase
from django.test import SimpleTestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.staticfiles import finders
from django.contrib.auth import get_user_model
from django.conf import settings

from config.backup import create_postgresql_backup


User = get_user_model()


class ProductionDeploymentContractTests(SimpleTestCase):
    def test_ci_runs_production_security_check(self):
        workflow = (
            Path(__file__).resolve().parent.parent
            / ".github"
            / "workflows"
            / "quality.yml"
        ).read_text()

        self.assertIn("check --deploy --fail-level ERROR", workflow)
        self.assertIn('DJANGO_DEBUG: "False"', workflow)
        self.assertNotIn("django-insecure-", workflow)

    def test_render_blueprint_uses_safe_release_sequence(self):
        blueprint = (Path(__file__).resolve().parent.parent / "render.yaml").read_text()

        self.assertIn("healthCheckPath: /health/ready/", blueprint)
        self.assertIn("preDeployCommand: python manage.py migrate --noinput", blueprint)
        self.assertIn("autoDeployTrigger: checksPass", blueprint)
        self.assertIn("generateValue: true", blueprint)
        self.assertIn("fromDatabase:", blueprint)
        self.assertNotIn("DJANGO_SECRET_KEY=", blueprint)

    def test_build_does_not_run_database_migrations(self):
        build_script = (
            Path(__file__).resolve().parent.parent
            / "deployment"
            / "render_build.sh"
        ).read_text()

        self.assertIn("collectstatic --noinput", build_script)
        self.assertIn("check --deploy", build_script)
        self.assertNotIn("manage.py migrate", build_script)


class ReleaseReadinessCommandTests(SimpleTestCase):
    @override_settings(
        DEBUG=False,
        SECRET_KEY="production-secret-key-for-readiness-tests",
        ALLOWED_HOSTS=["app.example.com"],
        CSRF_TRUSTED_ORIGINS=["https://app.example.com"],
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=3600,
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_HOST="smtp.example.com",
        EMAIL_HOST_USER="mailer",
        EMAIL_HOST_PASSWORD="secret",
        DEFAULT_FROM_EMAIL="Table Tennis Manager <noreply@example.com>",
        LEGAL_CONTROLLER_NAME="Example Controller",
        LEGAL_CONTACT_EMAIL="privacy@example.com",
        LEGAL_COUNTRY="Brazil",
    )
    def test_release_readiness_accepts_complete_production_configuration(self):
        output = StringIO()

        production_database = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "table_tennis_manager",
            }
        }
        with patch.object(settings, "DATABASES", production_database):
            call_command("check_release_readiness", stdout=output)

        self.assertIn("Release configuration checks passed", output.getvalue())

    def test_release_readiness_blocks_local_development_configuration(self):
        with self.assertRaisesMessage(CommandError, "Release blocked"):
            call_command("check_release_readiness", stdout=StringIO())

    @override_settings(
        DEBUG=False,
        SECRET_KEY="production-secret-key-for-resend-tests",
        ALLOWED_HOSTS=["app.example.com"],
        CSRF_TRUSTED_ORIGINS=["https://app.example.com"],
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=3600,
        EMAIL_BACKEND="anymail.backends.resend.EmailBackend",
        ANYMAIL={"RESEND_API_KEY": "re_test_key"},
        DEFAULT_FROM_EMAIL="Table Tennis Manager <noreply@example.com>",
        LEGAL_CONTROLLER_NAME="Example Controller",
        LEGAL_CONTACT_EMAIL="privacy@example.com",
        LEGAL_COUNTRY="Brazil",
    )
    def test_release_readiness_accepts_resend_api_backend(self):
        production_database = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "table_tennis_manager",
            }
        }
        with patch.object(settings, "DATABASES", production_database):
            call_command("check_release_readiness", stdout=StringIO())

    @override_settings(
        EMAIL_BACKEND="anymail.backends.resend.EmailBackend",
        ANYMAIL={"RESEND_API_KEY": ""},
    )
    def test_release_readiness_rejects_resend_without_api_key(self):
        with self.assertRaisesMessage(CommandError, "Release blocked"):
            call_command("check_release_readiness", stdout=StringIO())


@override_settings(DEBUG=True)
class AcceptanceWorkspaceCommandTests(TestCase):
    def test_command_refuses_the_normal_database(self):
        with self.assertRaisesMessage(CommandError, "isolated database"):
            call_command("create_acceptance_workspace", stdout=StringIO())

    def test_command_creates_a_complete_isolated_demo(self):
        isolated_database = settings.DATABASES.copy()
        isolated_database["default"] = settings.DATABASES["default"].copy()
        isolated_database["default"]["NAME"] = "/tmp/ttm_acceptance-test.sqlite3"

        with patch.object(settings, "DATABASES", isolated_database):
            output = StringIO()
            call_command("create_acceptance_workspace", stdout=output)
            call_command("create_acceptance_workspace", stdout=output)

        user = User.objects.get(username="acceptance-demo")
        self.assertTrue(user.check_password("TableTennisDemo2026!"))
        self.assertEqual(user.players.count(), 1)
        self.assertEqual(user.matches.count(), 1)
        self.assertEqual(user.competitions.count(), 1)
        self.assertGreaterEqual(user.calendar_events.count(), 1)
        self.assertEqual(user.transactions.count(), 1)
        self.assertEqual(user.notes.count(), 1)
        self.assertIn("Acceptance workspace is ready", output.getvalue())


class MultilingualPageTitleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="title-audit",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_primary_page_titles_are_translated_in_spanish(self):
        expected_titles = {
            "/dashboard/": "Panel | Table Tennis Manager",
            "/matches/": "Partidos | Table Tennis Manager",
            "/planning/calendar/": "Calendario | Table Tennis Manager",
            "/finances/": "Finanzas | Table Tennis Manager",
            "/notes/": "Notas | Table Tennis Manager",
        }

        for path, expected_title in expected_titles.items():
            with self.subTest(path=path):
                response = self.client.get(
                    path,
                    HTTP_ACCEPT_LANGUAGE="es",
                )
                self.assertContains(response, expected_title)


class AccessibilityShellTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="accessibility-audit",
            email="accessibility@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)

    def test_application_has_one_banner_and_a_keyboard_skip_link(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, '<a class="skip-link" href="#main-content">')
        self.assertContains(
            response,
            '<main id="main-content" class="main-content" tabindex="-1">',
        )
        self.assertEqual(
            response.content.decode().count('<header class="site-header">'),
            1,
        )

    def test_primary_navigation_identifies_the_current_section(self):
        response = self.client.get(reverse("finances:list"))

        self.assertContains(response, 'aria-label="Primary navigation"')
        self.assertContains(
            response,
            f'href="{reverse("finances:list")}" aria-current="page"',
        )


class ProgressiveWebAppTests(TestCase):
    def test_root_favicon_redirects_to_the_static_brand_asset(self):
        response = self.client.get(reverse("favicon"))

        self.assertRedirects(
            response,
            "/static/icons/favicon.ico",
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_manifest_has_stable_identity_and_installable_assets(self):
        response = self.client.get(reverse("pwa-manifest"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        manifest = response.json()
        self.assertEqual(manifest["id"], "/")
        self.assertEqual(manifest["start_url"], reverse("dashboard:home"))
        self.assertEqual(manifest["scope"], "/")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(
            {icon["sizes"] for icon in manifest["icons"]},
            {"192x192", "512x512"},
        )
        self.assertIn(
            "maskable",
            {icon["purpose"] for icon in manifest["icons"]},
        )

    def test_manifest_is_localized(self):
        with self.settings(LANGUAGE_CODE="pt-br"):
            response = self.client.get(
                reverse("pwa-manifest"),
                HTTP_ACCEPT_LANGUAGE="pt-BR",
            )

        self.assertEqual(
            response.json()["description"],
            "Gerencie atletas, partidas, competições e desempenho.",
        )

    def test_service_worker_only_caches_public_static_assets(self):
        response = self.client.get(reverse("service-worker"))
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Service-Worker-Allowed"], "/")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn('request.mode === "navigate"', content)
        self.assertIn('url.pathname.startsWith("/static/")', content)
        self.assertIn("fetch(request).catch", content)

    def test_service_worker_uses_current_static_cache_version(self):
        response = self.client.get(reverse("service-worker"))

        self.assertContains(response, 'CACHE_VERSION = "ttm-static-v6"')

    def test_stylesheet_url_changes_with_the_current_interface_release(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertContains(response, "/static/css/styles.css?v=6")

    def test_offline_page_explains_data_protection(self):
        response = self.client.get(
            reverse("offline"),
            HTTP_ACCEPT_LANGUAGE="pt-BR",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Suas informações privadas")

    def test_required_icons_have_exact_dimensions(self):
        expected = {
            "icons/icon-192.png": (192, 192),
            "icons/icon-512.png": (512, 512),
            "icons/icon-maskable-512.png": (512, 512),
            "icons/apple-touch-icon.png": (180, 180),
            "icons/brand-mark.png": (256, 256),
        }

        for asset, dimensions in expected.items():
            with self.subTest(asset=asset):
                path = finders.find(asset)
                self.assertIsNotNone(path)
                with Path(path).open("rb") as icon_file:
                    header = icon_file.read(24)
                self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", header[16:24]), dimensions)

    def test_finance_table_is_contained_on_small_screens(self):
        stylesheet = (
            Path(__file__).resolve().parent.parent
            / "static"
            / "css"
            / "styles.css"
        ).read_text()

        self.assertIn(".finance-page {", stylesheet)
        self.assertIn("overscroll-behavior-inline: contain", stylesheet)
        self.assertIn("-webkit-overflow-scrolling: touch", stylesheet)
        self.assertIn(".finance-table .sr-only", stylesheet)


class HealthCheckTests(TestCase):
    def test_health_check_reports_database_as_available(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Cache-Control"], "max-age=0, no-cache, no-store, must-revalidate, private")

    @patch("config.views.connections")
    def test_health_check_reports_database_failure(self, mocked_connections):
        mocked_connections[
            "default"
        ].cursor.side_effect = OperationalError

        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})

    def test_liveness_does_not_query_database(self):
        with patch("config.views.connections") as mocked_connections:
            response = self.client.get(reverse("liveness-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        mocked_connections.assert_not_called()

    def test_readiness_checks_database(self):
        response = self.client.get(reverse("readiness-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class DatabaseBackupTests(TestCase):
    def test_sqlite_backup_is_created_and_verified(self):
        with TemporaryDirectory() as directory:
            output = StringIO()
            call_command(
                "backup_database",
                directory=directory,
                stdout=output,
            )
            backup_files = list(Path(directory).glob("*.sqlite3"))

            self.assertEqual(len(backup_files), 1)
            backup_path = backup_files[0]
            self.assertTrue(
                backup_path.with_suffix(".sqlite3.json").is_file()
            )

            verify_output = StringIO()
            call_command(
                "verify_backup",
                str(backup_path),
                stdout=verify_output,
            )
            self.assertIn("Backup verified", verify_output.getvalue())

    def test_verification_rejects_modified_backup(self):
        with TemporaryDirectory() as directory:
            call_command(
                "backup_database",
                directory=directory,
                stdout=StringIO(),
            )
            backup_path = next(Path(directory).glob("*.sqlite3"))

            with backup_path.open("ab") as backup_file:
                backup_file.write(b"unexpected-change")

            with self.assertRaisesMessage(
                CommandError,
                "Backup size does not match its metadata.",
            ):
                call_command(
                    "verify_backup",
                    str(backup_path),
                    stdout=StringIO(),
                )

    @override_settings(PG_DUMP_BINARY="pg_dump-custom")
    @patch("config.backup.subprocess.run")
    @patch("config.backup.connection")
    def test_postgresql_backup_keeps_password_out_of_command(
        self,
        mocked_connection,
        mocked_run,
    ):
        mocked_connection.settings_dict = {
            "NAME": "manager",
            "HOST": "database.example.com",
            "PORT": "5432",
            "USER": "manager_user",
            "PASSWORD": "private-password",
        }

        create_postgresql_backup(Path("backup.partial"))

        command = mocked_run.call_args.args[0]
        environment = mocked_run.call_args.kwargs["env"]
        self.assertNotIn("private-password", command)
        self.assertEqual(environment["PGPASSWORD"], "private-password")
        self.assertIn("--format=custom", command)
        mocked_run.assert_called_once()

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import struct

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import OperationalError
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.staticfiles import finders

from config.backup import create_postgresql_backup


class ProgressiveWebAppTests(TestCase):
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

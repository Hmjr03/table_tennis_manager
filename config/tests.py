from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.utils import OperationalError
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from config.backup import create_postgresql_backup


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

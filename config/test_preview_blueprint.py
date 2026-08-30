from pathlib import Path
from unittest import TestCase


class PreviewBlueprintTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = (
            Path(__file__).resolve().parent.parent / "render.preview.yaml"
        ).read_text(encoding="utf-8")

    def test_preview_uses_only_free_plans(self):
        self.assertEqual(self.content.count("plan: free"), 2)
        self.assertNotIn("plan: starter", self.content)
        self.assertNotIn("plan: basic-", self.content)
        self.assertNotIn("maxShutdownDelaySeconds", self.content)

    def test_preview_resources_are_isolated(self):
        self.assertIn("name: table-tennis-manager-preview", self.content)
        self.assertIn("name: table-tennis-manager-preview-db", self.content)
        self.assertNotIn("name: table-tennis-manager-db\n", self.content)

    def test_preview_does_not_require_smtp_secrets(self):
        self.assertIn(
            "value: django.core.mail.backends.console.EmailBackend",
            self.content,
        )
        self.assertNotIn("DJANGO_EMAIL_HOST_PASSWORD", self.content)

    def test_preview_runs_migrations_before_starting(self):
        self.assertIn(
            "startCommand: python manage.py migrate --noinput && gunicorn",
            self.content,
        )

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Audit the configuration required for a safe production release."

    def handle(self, *args, **options):
        smtp_backend = "django.core.mail.backends.smtp.EmailBackend"
        resend_backend = "anymail.backends.resend.EmailBackend"
        email_backend_supported = settings.EMAIL_BACKEND in {
            smtp_backend,
            resend_backend,
        }
        if settings.EMAIL_BACKEND == smtp_backend:
            email_credentials_configured = all(
                (
                    settings.EMAIL_HOST,
                    settings.EMAIL_HOST_USER,
                    settings.EMAIL_HOST_PASSWORD,
                )
            )
        elif settings.EMAIL_BACKEND == resend_backend:
            email_credentials_configured = bool(
                settings.ANYMAIL.get("RESEND_API_KEY")
            )
        else:
            email_credentials_configured = False

        checks = [
            (not settings.DEBUG, "Debug mode is disabled"),
            (
                bool(settings.SECRET_KEY)
                and not settings.SECRET_KEY.startswith("django-insecure-"),
                "A production secret key is configured",
            ),
            (
                bool(settings.ALLOWED_HOSTS)
                and "*" not in settings.ALLOWED_HOSTS,
                "Allowed hosts are explicit",
            ),
            (
                bool(settings.CSRF_TRUSTED_ORIGINS)
                and all(
                    origin.startswith("https://")
                    for origin in settings.CSRF_TRUSTED_ORIGINS
                ),
                "Trusted origins use HTTPS",
            ),
            (getattr(settings, "SESSION_COOKIE_SECURE", False), "Session cookies require HTTPS"),
            (getattr(settings, "CSRF_COOKIE_SECURE", False), "CSRF cookies require HTTPS"),
            (getattr(settings, "SECURE_SSL_REDIRECT", False), "HTTP is redirected to HTTPS"),
            (
                getattr(settings, "SECURE_HSTS_SECONDS", 0) > 0,
                "HTTP Strict Transport Security is enabled",
            ),
            (
                settings.DATABASES["default"]["ENGINE"]
                != "django.db.backends.sqlite3",
                "A production database is configured",
            ),
            (email_backend_supported, "A production email backend is configured"),
            (
                email_credentials_configured,
                "Email provider credentials are configured",
            ),
            (
                "localhost" not in settings.DEFAULT_FROM_EMAIL,
                "The sender address uses a real domain",
            ),
            (
                bool(settings.LEGAL_CONTROLLER_NAME)
                and bool(settings.LEGAL_CONTACT_EMAIL)
                and bool(settings.LEGAL_COUNTRY),
                "Legal controller details are configured",
            ),
        ]

        failed = []
        for passed, description in checks:
            marker = self.style.SUCCESS("PASS") if passed else self.style.ERROR("FAIL")
            self.stdout.write(f"[{marker}] {description}")
            if not passed:
                failed.append(description)

        if failed:
            raise CommandError(
                f"Release blocked: {len(failed)} required configuration "
                f"check(s) failed."
            )

        self.stdout.write(
            self.style.SUCCESS("Release configuration checks passed.")
        )

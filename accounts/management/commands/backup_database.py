from django.conf import settings
from django.core.management.base import BaseCommand

from config.backup import create_database_backup


class Command(BaseCommand):
    help = "Create a consistent database backup and SHA-256 metadata."

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory",
            default=settings.BACKUP_ROOT,
            help="Directory where the backup will be stored.",
        )

    def handle(self, *args, **options):
        backup_path = create_database_backup(options["directory"])
        self.stdout.write(
            self.style.SUCCESS(f"Backup created: {backup_path}")
        )

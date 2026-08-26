from django.core.management.base import BaseCommand

from config.backup import verify_database_backup


class Command(BaseCommand):
    help = "Verify a backup checksum and database structure."

    def add_arguments(self, parser):
        parser.add_argument("backup_path")

    def handle(self, *args, **options):
        metadata = verify_database_backup(options["backup_path"])
        self.stdout.write(
            self.style.SUCCESS(
                "Backup verified: "
                f"{metadata['filename']} ({metadata['size_bytes']} bytes)"
            )
        )

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError
from django.db import connection
from django.utils import timezone


def file_sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as backup_file:
        for chunk in iter(lambda: backup_file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def backup_filename(vendor):
    timestamp = timezone.now().strftime("%Y%m%dT%H%M%SZ")
    extension = "sqlite3" if vendor == "sqlite" else "dump"
    return f"table_tennis_manager_{timestamp}_{vendor}.{extension}"


def create_sqlite_backup(target):
    connection.ensure_connection()
    destination = sqlite3.connect(target)

    try:
        connection.connection.backup(destination)
    finally:
        destination.close()


def create_postgresql_backup(target):
    database = connection.settings_dict
    command = [
        settings.PG_DUMP_BINARY,
        "--format=custom",
        "--no-owner",
        "--no-acl",
        f"--file={target}",
    ]

    option_map = {
        "HOST": "--host",
        "PORT": "--port",
        "USER": "--username",
    }
    for setting_name, option in option_map.items():
        value = database.get(setting_name)
        if value:
            command.append(f"{option}={value}")

    command.append(database["NAME"])
    environment = os.environ.copy()
    if database.get("PASSWORD"):
        environment["PGPASSWORD"] = database["PASSWORD"]

    try:
        subprocess.run(
            command,
            check=True,
            env=environment,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise CommandError(
            "pg_dump was not found. Configure DJANGO_PG_DUMP_BINARY."
        ) from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or "pg_dump failed"
        raise CommandError(detail) from error


def create_database_backup(directory):
    directory = Path(directory).expanduser().resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    vendor = connection.vendor

    if vendor not in {"sqlite", "postgresql"}:
        raise CommandError(
            f"Database engine '{vendor}' is not supported for backups."
        )

    final_path = directory / backup_filename(vendor)
    temporary_path = final_path.with_suffix(final_path.suffix + ".partial")

    try:
        if vendor == "sqlite":
            create_sqlite_backup(temporary_path)
        else:
            create_postgresql_backup(temporary_path)

        temporary_path.chmod(0o600)
        temporary_path.replace(final_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    metadata = {
        "application": "Table Tennis Manager",
        "created_at": timezone.now().isoformat(),
        "database_engine": vendor,
        "filename": final_path.name,
        "size_bytes": final_path.stat().st_size,
        "sha256": file_sha256(final_path),
    }
    metadata_path = final_path.with_suffix(final_path.suffix + ".json")
    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    metadata_path.chmod(0o600)
    return final_path


def verify_database_backup(backup_path):
    backup_path = Path(backup_path).expanduser().resolve()
    metadata_path = backup_path.with_suffix(backup_path.suffix + ".json")

    if not backup_path.is_file():
        raise CommandError(f"Backup file not found: {backup_path}")
    if not metadata_path.is_file():
        raise CommandError(f"Backup metadata not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if backup_path.stat().st_size != metadata.get("size_bytes"):
        raise CommandError("Backup size does not match its metadata.")
    if file_sha256(backup_path) != metadata.get("sha256"):
        raise CommandError("Backup checksum verification failed.")

    engine = metadata.get("database_engine")
    if engine == "sqlite":
        database = sqlite3.connect(
            f"file:{backup_path}?mode=ro",
            uri=True,
        )
        try:
            result = database.execute("PRAGMA quick_check").fetchone()
        finally:
            database.close()
        if not result or result[0] != "ok":
            raise CommandError("SQLite integrity verification failed.")
    elif engine == "postgresql":
        try:
            subprocess.run(
                [settings.PG_RESTORE_BINARY, "--list", str(backup_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as error:
            raise CommandError(
                "pg_restore was not found. Configure "
                "DJANGO_PG_RESTORE_BINARY."
            ) from error
        except subprocess.CalledProcessError as error:
            detail = error.stderr.strip() or "pg_restore validation failed"
            raise CommandError(detail) from error
    else:
        raise CommandError("Backup metadata contains an unknown engine.")

    return metadata

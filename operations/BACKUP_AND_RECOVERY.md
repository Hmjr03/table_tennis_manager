# Backup and recovery runbook

This runbook protects Table Tennis Manager data. Backups contain personal,
financial and sports information and must be treated as confidential.

## Recovery objectives

- Create at least one automated database backup every 24 hours.
- Keep a second encrypted copy outside the application server.
- Retain daily, weekly and monthly recovery points according to the hosting
  provider and legal retention policy.
- Test a restore into an isolated database at least once every three months.
- Record the date, operator, backup identifier and verification result.

## Create and verify a backup

```bash
python manage.py backup_database
python manage.py verify_backup /absolute/path/to/backup-file
```

Each backup has a matching `.json` file containing its size and SHA-256
checksum. Verification checks both the checksum and the database structure.
The command never removes previous backups.

## Storage controls

1. Do not commit backups to Git.
2. Keep the local backup directory accessible only to the service account.
3. Upload a second copy to encrypted object storage with versioning enabled.
4. Restrict restore and deletion permissions to designated administrators.
5. Monitor failed scheduled backups and unexpected changes in backup size.

## Safe restore test

Never test a restore over the live database. Restore into a new isolated
database, run migrations and checks, compare key record counts, and only then
mark the recovery point as tested.

For PostgreSQL, create an empty test database and restore the custom dump:

```bash
createdb table_tennis_manager_restore_test
pg_restore --no-owner --no-acl --dbname table_tennis_manager_restore_test /absolute/path/to/backup.dump
```

For SQLite development backups, copy the verified `.sqlite3` file to a
temporary project environment and run:

```bash
python manage.py check
python manage.py showmigrations --plan
```

## Production incident recovery

Production restoration requires an approved maintenance window, a fresh
backup of the current state, confirmation of the exact target database, and a
rollback plan. Prefer the managed database provider's point-in-time recovery
feature. Do not overwrite the production database directly from a developer
computer.

After restoration:

1. Run `python manage.py migrate --check`.
2. Verify `/health/ready/` returns `{"status": "ok"}`.
3. Check account, player, match, competition and transaction counts.
4. Perform a controlled login and read-only smoke test.
5. Document the recovery and notify affected users when legally required.

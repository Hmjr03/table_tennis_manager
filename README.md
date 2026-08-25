# Table Tennis Manager

A professional web platform for table tennis athletes, coaches, and clubs.

## Vision

Table Tennis Manager aims to provide tools for:

- Athlete management
- Match tracking
- Ranking management
- Performance statistics
- Tournament management
- Training planning
- Calendar management
- Performance analysis

## Tech Stack

- Python
- Django
- PostgreSQL
- HTML
- CSS
- JavaScript

## Status

🚧 Project under development.

## Local setup

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and set local values.
3. Run migrations with `python manage.py migrate`.
4. Start the development server with `python manage.py runserver 8001`.

Operational endpoints:

- `/health/live/` confirms that the web process is responding.
- `/health/ready/` confirms that the application can reach its database.
- `/health/` remains the backward-compatible readiness endpoint.

Create and verify a local backup:

```bash
python manage.py backup_database
python manage.py verify_backup /absolute/path/to/backup-file
```

See `operations/BACKUP_AND_RECOVERY.md` for storage and restore procedures.

## Production readiness

Before publishing, configure PostgreSQL through `DATABASE_URL`, use a unique
secret key, disable debug mode, configure the production host and trusted HTTPS
origin, and provide a real email service. Production must also have automated
database backups, uptime/error monitoring, and a tested restore procedure.

Run the deployment validation before every release:

```bash
python manage.py check --deploy
python manage.py migrate --check
python manage.py test
```

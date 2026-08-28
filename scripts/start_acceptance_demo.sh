#!/usr/bin/env bash
set -euo pipefail

export DATABASE_URL="sqlite:////tmp/ttm_acceptance.sqlite3"
export DJANGO_DEBUG="True"

python manage.py migrate --noinput
python manage.py create_acceptance_workspace
python manage.py runserver 8001

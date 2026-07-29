#!/bin/sh
set -eu

: "${PORT:=8000}"
: "${WEB_CONCURRENCY:=2}"
: "${RUN_MIGRATIONS_ON_START:=1}"

if [ "${RUN_MIGRATIONS_ON_START}" = "1" ]; then
  python manage.py migrate --noinput
  python manage.py seed_data
fi

exec gunicorn arizauz.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -

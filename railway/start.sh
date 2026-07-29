#!/bin/sh
set -eu

: "${PORT:=8000}"
: "${WEB_CONCURRENCY:=2}"

exec gunicorn arizauz.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -

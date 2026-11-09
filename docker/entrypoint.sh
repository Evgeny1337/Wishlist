#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
# 1 worker — экономия RAM на маленьком VPS (~3 ГБ свободно)
exec gunicorn wishlist.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-1}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout 60

#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE=config.settings

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec daphne -b 0.0.0.0 -p 8000 config.asgi:application

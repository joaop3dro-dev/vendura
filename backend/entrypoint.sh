#!/bin/sh
while ! python manage.py migrate --noinput; do
    sleep 1
done
exec "$@"

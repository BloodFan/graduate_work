#!/bin/sh
cd /opt/profiles_app/src
alembic upgrade head

# python scripts/create_initial_data.py

cd /opt/profiles_app

nginx -g 'daemon on;'

exec "$@"
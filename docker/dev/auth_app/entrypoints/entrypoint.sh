#!/bin/sh
cd /opt/auth_app/src
alembic upgrade head

python scripts/create_superuser.py

cd /opt/auth_app

nginx -g 'daemon on;'

exec "$@"
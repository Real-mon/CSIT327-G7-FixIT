#!/usr/bin/env bash
set -0 errexit
pip install -r requirements.txt

npm ci

npm run build

python manage.py collectstatic --noinput

python manage.py migrate



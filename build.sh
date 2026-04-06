#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py makemigrations chat accounts jobs reviews payments courses blog dashboard notifications
python manage.py migrate
python create_admin.py

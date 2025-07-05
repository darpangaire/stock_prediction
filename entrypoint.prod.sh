#!/bin/bash
python manage.py collectstatic --noinput
python manage.py migrate
python -m gunicorn --bind 0.0.0.0:8000 --workers 3 stock_prediction.wsgi:application

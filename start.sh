#!/bin/sh
python3 manage.py makemigrations main
python3 manage.py migrate

# python3 manage.py runserver 80
uwsgi --module=GifExplorer.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=GifExplorer.settings \
    --master \
    --http=0.0.0.0:80 \
    --processes=5 \
    --harakiri=40 \
    --max-requests=5000 \
    --vacuum

#!/bin/sh
python -m http.server 10000 &
celery -A app.core.celery_app worker --loglevel=info --pool=threads
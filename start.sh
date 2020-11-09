service redis-server start
python manage.py runserver 0.0.0.0:8000 & celery -A music.celery_task.celery worker --loglevel=info

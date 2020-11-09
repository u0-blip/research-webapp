sudo service redis-server start
python manage.py runserver & celery -A music.celery_task.celery worker --loglevel=info

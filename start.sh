sudo service redis-server start
celery -A music.celery_task.celery worker --loglevel=info & gunicorn --bind 127.0.0.1:8000 research_webapp_back.wsgi &

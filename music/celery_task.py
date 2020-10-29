from sqlalchemy import update
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, flash, request, url_for, jsonify, session, redirect, send_file, send_from_directory
from wtforms import Form, TextField, validators, StringField, SubmitField, fields, FormField
from wtforms.validators import Optional
from celery import Celery
import matplotlib.pyplot as plt
import numpy as np
import redis
from time import time
import os
import sys

# from basic_app import app
# from models.user_models import User
# from models.data_models import Input_data, Radio_data, Check_data, Range_data

# sys.path.append('/mnt/c/peter_abaqus/Summer-Research-Project/')

# from my_meep.wsl_main import wsl_main
# from my_meep.config.configs import config

# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)
# from default_value import sections_name
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'research_webapp_back.settings')

celery = Celery('research_webapp_back')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery.config_from_object('django.conf:settings', namespace='CELERY')
 
# def update_configs(current_user):
#     user = User.query.filter(User.id == current_user).first()
#     for v in user.range_data:
#         config.set(v.section, v.spec, ', '.join([str(v.start), str(v.stop), str(v.steps)]))
#     for v in user.input_data:
#         config.set(v.section, v.spec, str(v.value))
#     for v in user.radio_data:
#         config.set(v.section, v.spec, str(v.value))
#     for v in user.check_data:
#         config.set(v.section, v.spec, str(v.value))

#     return config

@celery.task(bind=True)
def long_task(self, current_user):
    message = ''
    prev = time()
    # for i, total, res in wsl_main(update_configs(current_user), current_user):
    #     i = int(i+1)
    #     total = int(total)

    #     now = time()
    #     elapsed = (now - prev)/1000
    #     prev = now
    #     sim_left = total - i
    #     projected_time = sim_left*elapsed

    #     message = 'Last simulation took {:.2f}s. Estimated total time left is {:.2f}'.format(elapsed, projected_time)

    #     self.update_state(state='PROGRESS',
    #                       meta={'current': i, 'total': total,
    #                             'status': message})

    return {'current': 1, 'total': 3, 'status': 'All simulation is done!', 'result':True}


def taskstatus(task_id):
    task = long_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

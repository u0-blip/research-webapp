from sqlalchemy import update
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, flash, request, url_for, jsonify, session, redirect, send_file, send_from_directory
from wtforms import Form, TextField, validators, StringField, SubmitField, fields, FormField
from wtforms.validators import Optional
from django.http import HttpResponse, Http404
from celery import Celery
import matplotlib.pyplot as plt
import numpy as np
import redis
from time import time
import os
import sys
import json
import redis
from copy import deepcopy

r = redis.Redis(host = 'meep_celery', port = 6379, db=0)
from my_meep.wsl_main import wsl_main
from my_meep.config.configs import primitive_config
# pip install --user -e .


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
 
def update_configs(web_config):
    config = deepcopy(primitive_config)
    sections_name = ['Visualization', 'General', 'Geometry', 'Simulation', 'Source']
    web_config_dict = {}
    if type(web_config) is list:
        for i, conf in enumerate(web_config):
            web_config_dict[i] = conf
    web_config = web_config_dict

    for i, keysection in enumerate(web_config.items()):
        sec_name = sections_name[i]
        key, section = keysection
        for type_field, fields  in section.items():
            if type_field == 'radio':
                for field_name, v in fields.items():
                    get = config.get(sec_name, field_name)
                    config.set(sec_name, field_name, str(v[0]))

    for i, keysection in enumerate(web_config.items()):
        sec_name = sections_name[i]
        key, section = keysection
        for type_field, fields  in section.items():
            if type_field in ['check', 'input'] :
                for field_name, v in fields.items():
                    get = config.get(sec_name, field_name)
                    config.set(sec_name, field_name, str(v))
            elif type_field in ['material_assign']:
                for field_name, v in fields.items():
                    get = config.get(sec_name, field_name)
                    sim_types = config.get('Simulation', 'sim_types')
                    config.set(sec_name, field_name, ', '.join([str(ele) for ele in v[sim_types]]))
            elif type_field not in ['radio']: #if type_field in ['range', 'coord', 'material']:
                for field_name, v in fields.items():
                    get = config.get(sec_name, field_name)
                    config.set(sec_name, field_name, ', '.join([str(ele) for ele in v]))
    return config

@celery.task(bind=True)
def meepsim(self, current_user):
    config = r.get('user_' + str(current_user)+'_current_config')
    config = json.loads(config)
    print('current user', current_user, config._sections)
    message = ''
    prev = time()
    for i, total, res in wsl_main(update_configs(config), current_user):
        i = int(i+1)
        total = int(total)

        now = time()
        elapsed = (now - prev)/1000
        prev = now
        sim_left = total - i
        projected_time = sim_left*elapsed

        message = 'Last simulation took {:.2f}s. Estimated total time left is {:.2f}'.format(elapsed, projected_time)

        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
    response = {'current': i, 'total': total, 'status': 'All simulation is done!', 'result':True}
    return response


def taskstatus(req, task_id):
    task = meepsim.AsyncResult(task_id)
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
    return HttpResponse(json.dumps(response), status=200)

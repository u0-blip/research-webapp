from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, Http404
from django.shortcuts import render
from .forms import UploadFileForm
import os
import research_webapp_back.settings as settings
import uuid
from django.db import models
import uuid
import urllib.parse
import json
import redis
from music.celery_task import long_task
from django.http import JsonResponse
from django.urls import reverse

# Imaginary function to handle an uploaded file.

def handle_uploaded_file(f, name):
    with open('./database/'+name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def handle_delete_file(name):
    name = './database/' + name
    if os.path.exists(name):
        os.remove(name)
        return 200
    else:
        return 404

def music_file(request, id=None):
    if request.method == 'POST':
        id = uuid.uuid4().hex
        url = id + '.mp3'
        handle_uploaded_file(request.FILES['file'], url)
        return HttpResponse(json.dumps({'url': url}), status=200)
 
    elif request.method == 'GET':
        if id==None:
            return HttpResponse('Please provide id', status=404)

        file_path = os.path.join(settings.MEDIA_ROOT, id)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="audio/mpeg")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        raise Http404
    elif request.method == 'DELETE':
        status = handle_delete_file(id)
        return HttpResponse(status=status)

current_user =0
import io
def show_image(request, type_img):
    img = r.get(str(current_user) + type_img)
    print('in show image', str(current_user) + type_img)
    if img == None:
        return Http404('image not found')

    else:
        return HttpResponse(img, status=200)

r = redis.Redis(host = 'localhost', port = 6379, db=0)

def longtask(request):
    task = long_task.apply_async(kwargs={'current_user':current_user})
    return JsonResponse({}), 202, {'Location': reverse('taskstatus:task_id', task_id=task.id)}

def download_mean(request):
    bytes_obj = io.BytesIO(r.get(str(current_user) + 'mean_result'))
    bytes_obj.seek(0)
    response = HttpResponse(bytes_obj, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="mean.xlsx"'
    return response

def download_field(request):
    bytes_obj = io.BytesIO(r.get(str(current_user) + 'field_result'))
    bytes_obj.seek(0)
    response = HttpResponse(bytes_obj, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="field.xlsx"'
    return response

from django.db import models
from django.contrib.auth import get_user_model



class Music(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    hashtag = models.TextField(blank=True)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(get_user_model(), null=True, on_delete=models.CASCADE)



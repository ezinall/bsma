# Create your tasks here
from __future__ import absolute_import, unicode_literals
import time

from celery.schedules import crontab
from django.db.models import Q
from django.conf import settings
import requests

from bsma.celery import app
from .models import Article


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute=5, hour=0),
        check_rosstat,
    )


@app.task(ignore_result=True)
def check_rosstat():
    articles = Article.objects.filter(Q(product_id=1), (Q(extra__isnull=True) | ~Q(extra__devices=[])))
    for i, article in enumerate(articles, 1):
        imei = article.imei.replace('-', '')
        url = f'https://nottheapi.rosstat.cloud.rt.ru:8443/apiman-gateway/Byterg/getDeviceActivationStatus/1.0/{imei}'
        r = requests.get(url, auth=(settings.ROS_USER, settings.ROS_PASSWORD), params={'apikey': settings.ROS_API_KYE})
        time.sleep(1)

        if 'devices' in r.json():
            article.extra = r.json()
            article.save()

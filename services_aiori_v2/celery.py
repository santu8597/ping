import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'services_aiori_v2.settings')

app = Celery('services_aiori_v2')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()






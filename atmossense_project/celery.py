import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atmossense_project.settings')

app = Celery('atmossense_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

'''
    Celery is an asynchronous task queue/job queue based on distributed message passing.
'''
import os
from celery import Celery
from .settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GifExplorer.settings')

app = Celery('GifExplorer')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: ['GifExplorer.main'])

@app.task(bind=True)
def debug_task(self):
    '''
        The bind=True switch causes the first argument to be the task instance itself (self).
    '''
    print(f'Request: {self.request!r}')

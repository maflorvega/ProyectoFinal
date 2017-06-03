from celery import Celery
from datetime import timedelta
from redash import settings, __version__


celery = Celery('redash',
                broker=settings.CELERY_BROKER,
                include=['redash.tasks', 'redash.devspark.custom_tasks'])

celery_schedule = {
    'refresh_queries': {
        'task': 'redash.tasks.refresh_queries',
        'schedule': timedelta(seconds=30)
    },
    'cleanup_tasks': {
        'task': 'redash.tasks.cleanup_tasks',
        'schedule': timedelta(minutes=5)
    },
    'refresh_schemas': {
        'task': 'redash.tasks.refresh_schemas',
        'schedule': timedelta(minutes=30)
    }
}

if settings.QUERY_RESULTS_CLEANUP_ENABLED:
    celery_schedule['cleanup_query_results'] = {
        'task': 'redash.tasks.cleanup_query_results',
        'schedule': timedelta(minutes=5)
    }

celery.conf.update(CELERY_RESULT_BACKEND=settings.CELERY_BACKEND,
                   CELERYBEAT_SCHEDULE=celery_schedule,
                   CELERY_TIMEZONE='UTC')

if settings.SENTRY_DSN:
    from raven import Client
    from raven.contrib.celery import register_signal, register_logger_signal

    client = Client(settings.SENTRY_DSN, release=__version__)
    register_signal(client)

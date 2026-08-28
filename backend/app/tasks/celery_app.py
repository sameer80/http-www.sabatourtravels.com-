from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery("ai_seo_manager", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = "UTC"
celery_app.conf.beat_schedule = {
    "daily-crawl-refresh": {
        "task": "app.tasks.scheduled.refresh_all_crawls",
        "schedule": crontab(hour=2, minute=0),
    },
    "daily-opportunity-refresh": {
        "task": "app.tasks.scheduled.refresh_all_opportunities",
        "schedule": crontab(hour=3, minute=0),
    },
}

celery_app.autodiscover_tasks(["app.tasks"])

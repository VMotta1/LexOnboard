import logging

from celery import Celery
from celery.signals import worker_ready

from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "lexonboard",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.process_document",
        "app.tasks.regenerate_playbook",
        "app.tasks.generate_onboarding",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours
)


@worker_ready.connect
def on_worker_ready(**kwargs):
    logger.info(
        "Celery worker ready. NLP models (LegalBERT ~400MB, CUAD-RoBERTa ~500MB) "
        "will be loaded lazily on first task execution."
    )
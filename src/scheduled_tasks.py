from typing import Callable
import services.review as rs
from datetime import timedelta
from flask.ctx import AppContext
from models.utils.utils import get_timestamp
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import JobExecutionEvent, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

ContextFun=Callable[[], AppContext]

def set_reviews_expired() -> None:
    rs.set_expired_status_for_reviews()

def set_context(callable: Callable[[], None], callable_context: ContextFun) -> Callable[[], None]:
    def _callable() -> None:
        with callable_context() as ctx:
            callable()
        del ctx
        return None
    return _callable

def job_listener(event: JobExecutionEvent) -> None:
    if event.exception:
        print(f"Job {event.job_id} failed")
    else:
        print(f"Job {event.job_id} completed successfully")

def create_scheduler(callable_context: ContextFun) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    # Uruchomienie 5s po starcie aplikacji (bez timedelta aplikacja potrafi się zawiesić)
    scheduler.add_job(set_context(set_reviews_expired, callable_context), DateTrigger(get_timestamp()+timedelta(seconds=5)))

    # Uruchamianie codziennie o północy
    scheduler.add_job(set_context(set_reviews_expired, callable_context), CronTrigger(hour=0, minute=0))

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.start()

    return scheduler

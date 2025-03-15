from typing import Callable
import services.review as rs
from flask.ctx import AppContext
from models.utils.utils import get_timestamp
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

    # Uruchomienie przy starcie aplikacji
    scheduler.add_job(set_context(set_reviews_expired, callable_context), 'date', run_date=get_timestamp())

    # Uruchamianie codziennie o północy
    scheduler.add_job(set_context(set_reviews_expired, callable_context), 'cron', hour=0, minute=0)

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.start()

    return scheduler

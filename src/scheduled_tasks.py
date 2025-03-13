from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import services.review as rs
from datetime import datetime

def set_reviews_expired():
    rs.set_expired_status_for_reviews()


def job_listener(event):
    if event.exception:
        print(f"Job {event.job_id} failed")
    else:
        print(f"Job {event.job_id} completed successfully")

def create_scheduler():
    scheduler = BackgroundScheduler()

    # Uruchomienie przy starcie aplikacji
    scheduler.add_job(set_reviews_expired, 'date', run_date=datetime.now())

    # Uruchamianie codziennie o północy
    scheduler.add_job(set_reviews_expired, 'cron', hour=0, minute=0)

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.start()

    return scheduler

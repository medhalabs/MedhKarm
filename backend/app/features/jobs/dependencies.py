from app.core.database import session_factory
from app.features.jobs.interfaces import JobQueue
from app.features.jobs.stores.sql_queue import SqlJobQueue


def get_job_queue() -> JobQueue:
    return SqlJobQueue(session_factory)

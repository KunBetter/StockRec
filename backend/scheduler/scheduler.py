import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.config import AppConfig
from backend.persistence.database import get_session
from backend.persistence.repository import Repository
from backend.persistence.models import ExecutionLog

logger = logging.getLogger(__name__)


class JobScheduler:
    def __init__(self, config: AppConfig):
        self.config = config
        self._scheduler = BackgroundScheduler(
            timezone=config.scheduler.timezone,
            job_defaults={"coalesce": True, "max_instances": 1},
        )

    def _log_start(self, job_name: str) -> int:
        session = get_session()
        repo = Repository(session, ExecutionLog)
        log = repo.create(
            job_name=job_name,
            started_at=datetime.utcnow(),
            status="running",
        )
        session.commit()
        session.close()
        return log.id

    def _log_end(self, log_id: int, status: str, records: int = 0, error: str = None):
        session = get_session()
        repo = Repository(session, ExecutionLog)
        log = repo.get_by_id(log_id)
        if log:
            log.finished_at = datetime.utcnow()
            log.status = status
            log.records_processed = records
            if error:
                log.error_message = error
            if log.started_at:
                log.duration_ms = int((log.finished_at - log.started_at).total_seconds() * 1000)
            session.commit()
        session.close()

    def register_hourly_update(self, job_func):
        job_cfg = self.config.scheduler.jobs.hourly_update
        if job_cfg.enabled:
            self._scheduler.add_job(
                self._wrap_job("hourly_update", job_func),
                CronTrigger.from_crontab(job_cfg.cron),
                id="hourly_update",
                name="Hourly Price & Score Update",
                replace_existing=True,
            )
            logger.info(f"Registered hourly_update job: {job_cfg.cron}")

    def register_daily_close(self, job_func):
        job_cfg = self.config.scheduler.jobs.daily_close
        if job_cfg.enabled:
            self._scheduler.add_job(
                self._wrap_job("daily_close", job_func),
                CronTrigger.from_crontab(job_cfg.cron),
                id="daily_close",
                name="Daily Close Processing",
                replace_existing=True,
            )
            logger.info(f"Registered daily_close job: {job_cfg.cron}")

    def register_model_retrain(self, job_func):
        job_cfg = self.config.scheduler.jobs.model_retrain
        if job_cfg.enabled:
            self._scheduler.add_job(
                self._wrap_job("model_retrain", job_func),
                CronTrigger.from_crontab(job_cfg.cron),
                id="model_retrain",
                name="Model Retraining",
                replace_existing=True,
            )
            logger.info(f"Registered model_retrain job: {job_cfg.cron}")

    def register_ai_analysis(self, job_func):
        job_cfg = self.config.scheduler.jobs.ai_analysis
        if job_cfg.enabled:
            self._scheduler.add_job(
                self._wrap_job("ai_analysis", job_func),
                CronTrigger.from_crontab(job_cfg.cron),
                id="ai_analysis",
                name="AI Analysis",
                replace_existing=True,
            )
            logger.info(f"Registered ai_analysis job: {job_cfg.cron}")

    def register_weekly_sync(self, job_func):
        job_cfg = self.config.scheduler.jobs.weekly_full_sync
        if job_cfg.enabled:
            self._scheduler.add_job(
                self._wrap_job("weekly_full_sync", job_func),
                CronTrigger.from_crontab(job_cfg.cron),
                id="weekly_full_sync",
                name="Weekly Full Sync",
                replace_existing=True,
            )
            logger.info(f"Registered weekly_full_sync job: {job_cfg.cron}")

    def _wrap_job(self, name: str, func):
        def wrapper():
            log_id = self._log_start(name)
            try:
                records = func(self.config)
                self._log_end(log_id, "success", records=records or 0)
            except Exception as e:
                logger.exception(f"Job {name} failed")
                self._log_end(log_id, "failed", error=str(e))

        return wrapper

    def start(self):
        self._scheduler.start()
        logger.info("Scheduler started")

    def shutdown(self):
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown")

    def get_jobs_status(self) -> list[dict]:
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            })
        return jobs

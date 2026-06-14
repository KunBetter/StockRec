from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config import load_config
from backend.persistence.database import get_engine, init_db
from backend.persistence.redis_client import init_redis, close_redis
from backend.api.router import api_router
from backend.api.endpoints.websocket import router as ws_router
from backend.scheduler.scheduler import JobScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    app.state.config = config

    root = Path(__file__).resolve().parent.parent
    log_path = root / config.logging.file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_path),
        level=config.logging.level,
        rotation=f"{config.logging.max_size_mb} MB",
        retention=config.logging.backup_count,
    )

    db_path = str(root / config.persistence.database.path)
    init_db(db_path)
    logger.info("Database initialized")
    app.state.db_engine = get_engine(db_path)

    if config.persistence.redis.enabled:
        await init_redis(config.persistence.redis.url)

    scheduler = JobScheduler(config)
    from backend.scheduler.jobs.hourly_update import run_hourly_update
    from backend.scheduler.jobs.daily_close import run_daily_close
    from backend.scheduler.jobs.weekly_full_sync import run_weekly_sync
    from backend.scheduler.jobs.model_retrain import run_model_retrain
    from backend.scheduler.jobs.ai_analysis_job import run_ai_analysis
    from backend.scheduler.jobs.run_strategy import run_strategy_scoring
    scheduler.register_hourly_update(run_hourly_update)
    scheduler.register_daily_close(run_daily_close)
    scheduler.register_strategy_scoring(run_strategy_scoring)
    scheduler.register_weekly_sync(run_weekly_sync)
    scheduler.register_model_retrain(run_model_retrain)
    scheduler.register_ai_analysis(run_ai_analysis)
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Scheduler started")

    yield

    scheduler.shutdown()
    await close_redis()
    logger.info("Shutting down")


app = FastAPI(
    title="鲸灵宝 API",
    description="AI深度选股 · 如鲸探宝",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(ws_router)


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "ok",
        "version": "0.1.0",
        "components": {
            "database": "connected",
            "scheduler": "running",
        },
    }

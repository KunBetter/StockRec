import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel


class BaostockConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 30
    retry_count: int = 3


class AkshareConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 30
    retry_count: int = 2


class SinaConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 10
    base_url: str = "http://hq.sinajs.cn"


class TencentConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 10
    base_url: str = "https://qt.gtimg.cn"


class DataSourcesConfig(BaseModel):
    baostock: BaostockConfig = BaostockConfig()
    akshare: AkshareConfig = AkshareConfig()
    sina: SinaConfig = SinaConfig()
    tencent: TencentConfig = TencentConfig()
    realtime_order: list[str] = ["akshare", "sina", "tencent"]
    history_order: list[str] = ["baostock", "akshare"]


class DatabaseConfig(BaseModel):
    url: str = ""  # postgresql+asyncpg://user:pass@host:5432/db
    url_sync: str = ""  # postgresql://user:pass@host:5432/db (for Alembic)
    path: str = "data/database/stockrec.db"  # fallback SQLite
    echo_sql: bool = False
    pool_size: int = 20
    max_overflow: int = 10


class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379/0"
    enabled: bool = True


class OSSConfig(BaseModel):
    endpoint: str = ""
    bucket: str = ""
    access_key_id: str = ""
    access_key_secret: str = ""
    enabled: bool = False


class ParquetConfig(BaseModel):
    base_path: str = "data/parquet"
    compression: str = "snappy"


class PersistenceConfig(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    oss: OSSConfig = OSSConfig()
    parquet: ParquetConfig = ParquetConfig()
    models: dict = {"path": "data/models"}


class LayerWeights(BaseModel):
    layer1_factor: float = 0.6
    layer2_ml: float = 0.3
    layer3_event: float = 0.1


class CompositeWeights(BaseModel):
    predicted_return: float = 0.5
    momentum_score: float = 0.2
    quality_score: float = 0.2
    sentiment_score: float = 0.1


class RiskClassification(BaseModel):
    low_threshold: int = 30
    medium_threshold: int = 60


class OutputConfig(BaseModel):
    top_n: int = 30
    max_per_industry_pct: float = 0.25


class FiltersConfig(BaseModel):
    exclude_st: bool = True
    exclude_suspended: bool = True
    exclude_limit_up_down: bool = True
    min_market_cap_billion: float = 10.0


class FactorsConfig(BaseModel):
    momentum_days: list[int] = [20, 60]
    volatility_days: int = 20
    turnover_days: int = 20


class StrategyConfig(BaseModel):
    stock_universe: str = "csi300_csi500"
    layer_weights: LayerWeights = LayerWeights()
    composite_score_weights: CompositeWeights = CompositeWeights()
    risk_classification: RiskClassification = RiskClassification()
    output: OutputConfig = OutputConfig()
    filters: FiltersConfig = FiltersConfig()
    factors: FactorsConfig = FactorsConfig()


class RateLimitConfig(BaseModel):
    requests_per_minute: int = 30
    max_concurrent: int = 3


class AIConfig(BaseModel):
    provider: str = "deepseek"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    max_tokens: int = 2000
    temperature: float = 0.3
    rate_limit: RateLimitConfig = RateLimitConfig()


class JobConfig(BaseModel):
    enabled: bool = True
    cron: str = ""


class SchedulerJobsConfig(BaseModel):
    hourly_update: JobConfig = JobConfig()
    daily_close: JobConfig = JobConfig()
    strategy_scoring: JobConfig = JobConfig()
    model_retrain: JobConfig = JobConfig()
    ai_analysis: JobConfig = JobConfig()
    weekly_full_sync: JobConfig = JobConfig()


class SchedulerConfig(BaseModel):
    timezone: str = "Asia/Shanghai"
    jobs: SchedulerJobsConfig = SchedulerJobsConfig()


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    log_level: str = "INFO"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/app.log"
    max_size_mb: int = 10
    backup_count: int = 5


class AppConfig(BaseModel):
    data_sources: DataSourcesConfig = DataSourcesConfig()
    persistence: PersistenceConfig = PersistenceConfig()
    strategy: StrategyConfig = StrategyConfig()
    ai: AIConfig = AIConfig()
    scheduler_cfg: SchedulerConfig = SchedulerConfig()
    server: ServerConfig = ServerConfig()
    logging: LoggingConfig = LoggingConfig()

    @property
    def scheduler(self) -> SchedulerConfig:
        return self.scheduler_cfg


_ENV_VAR_RE = re.compile(r"\$\{(\w+)(?::-([^}]*))?\}")


def _resolve_env(value: str) -> str:
    def _replace(match):
        var_name = match.group(1)
        default = match.group(2)
        return os.environ.get(var_name, default or "")

    return _ENV_VAR_RE.sub(_replace, value)


def _resolve_env_in_dict(data: dict) -> dict:
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = _resolve_env(v)
        elif isinstance(v, dict):
            result[k] = _resolve_env_in_dict(v)
        elif isinstance(v, list):
            result[k] = [
                _resolve_env(item) if isinstance(item, str) else item for item in v
            ]
        else:
            result[k] = v
    return result


def load_config(config_path: str = "config.yaml") -> AppConfig:
    root = Path(__file__).resolve().parent.parent
    full_path = root / config_path

    if full_path.exists():
        with open(full_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    else:
        raw = {}

    raw = _resolve_env_in_dict(raw)

    ai_raw = raw.get("ai", {})
    return AppConfig(
        data_sources=raw.get("data_sources", {}),
        persistence=raw.get("persistence", {}),
        strategy=raw.get("strategy", {}),
        ai=ai_raw,
        scheduler_cfg=raw.get("scheduler", {}),
        server=raw.get("server", {}),
        logging=raw.get("logging", {}),
    )

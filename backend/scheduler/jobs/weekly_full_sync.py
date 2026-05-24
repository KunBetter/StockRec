import logging

from backend.config import AppConfig
from backend.data.data_orchestrator import DataOrchestrator
from backend.persistence.database import get_session
from backend.persistence.repository import Repository
from backend.persistence.models import Stock

logger = logging.getLogger(__name__)


def run_weekly_sync(config: AppConfig) -> int:
    session = get_session()
    try:
        orch = DataOrchestrator(config)

        # Sync stock list
        stock_df = orch.sync_stock_list()
        if stock_df.empty:
            logger.warning("Failed to sync stock list")
            orch.cleanup()
            return 0

        # Sync industry data
        industry_df = orch.sync_stock_industry()
        industry_map = {}
        if not industry_df.empty:
            for _, row in industry_df.iterrows():
                industry_map[row.get("symbol", "")] = {
                    "industry": row.get("industry"),
                    "industry_code": row.get("industry_code"),
                }

        # Update stocks table
        stock_repo = Repository(session, Stock)
        inserted = 0
        for _, row in stock_df.iterrows():
            symbol = row.get("symbol", "")
            if not symbol:
                continue
            name = row.get("code_name", "")
            code = row.get("code", "")

            ind_info = industry_map.get(symbol, {})
            stock_repo.upsert(
                unique_keys={"symbol": symbol},
                data={
                    "code": code,
                    "name": name,
                    "exchange": symbol.split(".")[0] if "." in symbol else "",
                    "industry": ind_info.get("industry"),
                    "industry_code": ind_info.get("industry_code"),
                    "status": "active",
                },
            )
            inserted += 1

        session.commit()
        orch.cleanup()
        logger.info(f"Weekly sync: {inserted} stocks updated")
        return inserted
    finally:
        session.close()

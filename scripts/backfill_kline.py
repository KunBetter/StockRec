#!/usr/bin/env python3
"""Backfill historical K-line data for all tracked stocks."""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from backend.config import load_config
from backend.data.data_orchestrator import DataOrchestrator
from backend.persistence.database import get_session, init_db
from backend.persistence.repository import Repository
from backend.persistence.models import Stock
from backend.persistence.parquet_store import ParquetStore


def main():
    parser = argparse.ArgumentParser(description="Backfill historical K-line data")
    parser.add_argument("--start", default="2020-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="End date (default: today)")
    parser.add_argument("--symbols", nargs="*", help="Specific symbols to backfill (default: all)")
    parser.add_argument("--max", type=int, default=0, help="Max stocks to process (0 = all)")
    args = parser.parse_args()

    config = load_config()
    init_db(config.persistence.database.path)

    session = get_session()
    stock_repo = Repository(session, Stock)

    if args.symbols:
        stocks = []
        for sym in args.symbols:
            s = stock_repo.find_one_by(symbol=sym)
            if s:
                stocks.append(s)
    else:
        stocks = stock_repo.find_by(status="active")

    if args.max > 0:
        stocks = stocks[:args.max]

    if not stocks:
        print("No stocks found. Run weekly sync first to populate stock list.")
        sys.exit(1)

    end_date = args.end or date.today().strftime("%Y-%m-%d")
    orch = DataOrchestrator(config)
    parquet = ParquetStore(
        base_path=config.persistence.parquet.base_path,
        compression=config.persistence.parquet.compression,
    )

    for i, stock in enumerate(stocks):
        try:
            print(f"[{i+1}/{len(stocks)}] Fetching {stock.symbol} ({stock.name})...")
            df = orch.fetch_daily_kline(stock.symbol, args.start, end_date)
            if df.empty:
                print(f"  -> No data")
                continue

            parquet.write_kline(stock.symbol, df)
            date_range = parquet.symbol_date_range(stock.symbol)
            print(f"  -> {len(df)} rows, range: {date_range[0]} ~ {date_range[1]}")
        except Exception as e:
            print(f"  -> Error: {e}")

    orch.cleanup()
    session.close()
    print("Backfill complete.")


if __name__ == "__main__":
    main()

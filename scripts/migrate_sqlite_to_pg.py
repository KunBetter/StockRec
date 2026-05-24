#!/usr/bin/env python3
"""
SQLite → PostgreSQL data migration script.

Usage:
    DATABASE_URL_SYNC=postgresql://user:pass@host:5432/db \\
    python scripts/migrate_sqlite_to_pg.py [--sqlite-path data/database/stockrec.db]

Requires: pandas, sqlalchemy, psycopg2 (or asyncpg)
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from loguru import logger
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TABLE_ORDER = [
    "users",
    "stocks",
    "daily_kline_metadata",
    "financial_data",
    "factor_scores",
    "recommendations",
    "news_sentiment",
    "fund_flows",
    "execution_logs",
    "market_indices",
    "watchlist",
]


def get_sqlite_engine(path: str):
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        logger.error(f"SQLite database not found: {abs_path}")
        sys.exit(1)
    return create_engine(f"sqlite:///{abs_path}")


def get_pg_engine(url: str):
    if not url:
        logger.error("DATABASE_URL_SYNC not set")
        sys.exit(1)
    return create_engine(url, pool_pre_ping=True)


def migrate_table(table_name: str, sqlite_engine, pg_engine, dry_run: bool = False):
    """Migrate a single table from SQLite to PostgreSQL."""
    logger.info(f"Migrating table: {table_name}")

    # Read from SQLite
    try:
        df = pd.read_sql_table(table_name, sqlite_engine)
    except ValueError:
        logger.warning(f"Table {table_name} not found in SQLite, skipping")
        return 0

    if df.empty:
        logger.info(f"Table {table_name} is empty, skipping")
        return 0

    # Handle timestamp columns — SQLite stores as string, PG needs proper datetime
    for col in df.columns:
        if "created_at" in col or "updated_at" in col or "started_at" in col or "finished_at" in col or "last_login_at" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        elif "trade_date" in col or "report_date" in col or "news_date" in col or "calc_date" in col or "list_date" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

    row_count = len(df)
    logger.info(f"  {row_count} rows to migrate")

    if dry_run:
        logger.info(f"  [DRY RUN] Would insert {row_count} rows into {table_name}")
        return row_count

    # Insert into PostgreSQL
    with pg_engine.begin() as conn:
        # Disable FK checks temporarily
        if table_name == TABLE_ORDER[0]:
            pass  # first table

        # Use batch insert
        df.to_sql(
            table_name,
            conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=5000,
        )

    logger.info(f"  Inserted {row_count} rows into {table_name}")
    return row_count


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite to PostgreSQL")
    parser.add_argument(
        "--sqlite-path",
        default="data/database/stockrec.db",
        help="Path to SQLite database",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without inserting")
    parser.add_argument("--tables", nargs="*", help="Specific tables to migrate (default: all)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    sqlite_path = project_root / args.sqlite_path

    pg_url = os.environ.get("DATABASE_URL_SYNC", "")
    if not pg_url:
        logger.error("DATABASE_URL_SYNC env var is required")
        sys.exit(1)

    sqlite_engine = get_sqlite_engine(str(sqlite_path))
    pg_engine = get_pg_engine(pg_url)

    # Verify PG connection
    with pg_engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        logger.info(f"Connected to PostgreSQL: {result.scalar()[:60]}...")

    # Verify SQLite connection
    with sqlite_engine.connect() as conn:
        result = conn.execute(text("SELECT sqlite_version()"))
        logger.info(f"Connected to SQLite: v{result.scalar()}")

    # Verify PG tables exist (Alembic should have been run)
    with pg_engine.connect() as conn:
        result = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        pg_tables = {r[0] for r in result}
        if not pg_tables:
            logger.error("No tables found in PostgreSQL. Run `alembic upgrade head` first.")
            sys.exit(1)
        logger.info(f"Existing PG tables: {pg_tables}")

    tables = args.tables or TABLE_ORDER
    total = 0

    for table in tables:
        count = migrate_table(table, sqlite_engine, pg_engine, args.dry_run)
        total += count

    logger.info(f"Total rows migrated: {total}")

    # Reset sequences for auto-increment columns
    if not args.dry_run:
        with pg_engine.connect() as conn:
            for table in tables:
                try:
                    conn.execute(
                        text(
                            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                            f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                        )
                    )
                except Exception:
                    pass
            conn.commit()
        logger.info("Auto-increment sequences reset")

    logger.info("Migration complete!")
    sqlite_engine.dispose()
    pg_engine.dispose()


if __name__ == "__main__":
    main()

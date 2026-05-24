#!/usr/bin/env python3
"""Initialize the StockRec database schema."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.persistence.database import init_db
from backend.config import load_config


def main():
    config = load_config()
    db_path = config.persistence.database.path
    print(f"Initializing database at: {db_path}")
    engine = init_db(db_path)
    print("Database initialized successfully.")

    from backend.persistence.models import Base
    tables = Base.metadata.tables.keys()
    print(f"Tables created: {', '.join(sorted(tables))}")


if __name__ == "__main__":
    main()

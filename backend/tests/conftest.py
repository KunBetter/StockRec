import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.persistence.database import get_engine, init_db, Base, get_session


@pytest.fixture(scope="function")
def test_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        engine = init_db(db_path)
        yield db_path
        # Cleanup
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def sample_stock_data():
    return {
        "symbol": "sh600000",
        "code": "600000",
        "name": "浦发银行",
        "exchange": "sh",
        "industry": "银行",
        "market_cap": 300000000000,
        "status": "active",
    }

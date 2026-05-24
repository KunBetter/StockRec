import os
import tempfile
from datetime import date, timedelta

import pandas as pd
import pytest

from backend.persistence.parquet_store import ParquetStore


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ParquetStore(base_path=tmpdir, compression="snappy")


def test_write_and_read_kline(store):
    dates = pd.date_range("2025-01-01", periods=10, freq="B")
    df = pd.DataFrame({
        "trade_date": dates,
        "open": [10.0 + i * 0.1 for i in range(10)],
        "high": [10.5 + i * 0.1 for i in range(10)],
        "low": [9.8 + i * 0.1 for i in range(10)],
        "close": [10.2 + i * 0.1 for i in range(10)],
        "volume": [1000000 + i * 10000 for i in range(10)],
        "amount": [10000000.0 + i * 100000 for i in range(10)],
        "pct_change": [0.5] * 10,
        "turn_rate": [1.2] * 10,
    })
    df["symbol"] = "sh600000"

    store.write_kline("sh600000", df)
    result = store.read_kline("sh600000")

    assert not result.empty
    assert len(result) == 10
    assert "trade_date" in result.columns
    assert "open" in result.columns


def test_read_empty_symbol(store):
    result = store.read_kline("nonexistent")
    assert result.empty


def test_list_symbols(store):
    df = pd.DataFrame({
        "trade_date": [date.today()],
        "open": [10.0], "high": [10.5], "low": [9.8], "close": [10.2],
        "volume": [1000000], "amount": [10000000.0],
    })
    store.write_kline("sh600000", df)
    store.write_kline("sz000001", df)

    symbols = store.list_symbols()
    assert "sh600000" in symbols
    assert "sz000001" in symbols


def test_date_range(store):
    dates = pd.date_range("2025-01-01", periods=30, freq="B")
    df = pd.DataFrame({
        "trade_date": dates,
        "open": [10.0] * 30, "high": [10.5] * 30, "low": [9.8] * 30, "close": [10.2] * 30,
        "volume": [1000000] * 30, "amount": [10000000.0] * 30,
    })
    store.write_kline("sh600000", df)

    start, end = store.symbol_date_range("sh600000")
    assert start is not None
    assert end is not None

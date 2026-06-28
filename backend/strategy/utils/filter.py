import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def filter_stocks(
    df: pd.DataFrame,
    exclude_st: bool = True,
    exclude_suspended: bool = True,
    exclude_limit_up_down: bool = True,
    min_market_cap_billion: float = 10.0,
) -> pd.DataFrame:
    result = df.copy()
    initial_count = len(result)

    if exclude_st and "is_st" in result.columns:
        result = result[result["is_st"] != True]
        if "isST" in result.columns:
            result = result[result["isST"] != "1"]

    if exclude_suspended:
        if "trade_status" in result.columns:
            result = result[result["trade_status"] == "1"]

    if exclude_limit_up_down:
        if "pct_change" in result.columns:
            result = result[result["pct_change"].abs() < 9.5]

    if min_market_cap_billion > 0 and "market_cap" in result.columns:
        min_cap = min_market_cap_billion * 1e9
        result = result[result["market_cap"] >= min_cap]

    removed = initial_count - len(result)
    if removed > 0:
        logger.info(f"Filtered out {removed} stocks (ST/suspended/limit/small-cap)")
    return result


def filter_by_universe(
    df: pd.DataFrame,
    universe: str = "csi300_csi500",
) -> pd.DataFrame:
    if universe == "all_a_shares":
        return df
    if universe == "csi300_csi500":
        # Exclude indices, ETFs, and non-stock symbols
        if "symbol" in df.columns:
            def _is_real_stock(sym):
                code = sym.split(".")[-1] if "." in sym else sym
                exchange = sym.split(".")[0] if "." in sym else ""
                # Exclude SH indices (sh.000xxx) but keep SZ real stocks (sz.000xxx)
                if exchange == "sh" and code.startswith("000"):
                    return False
                # Exclude all 399xxx indices (both SH and SZ)
                if code.startswith("399"):
                    return False
                # Exclude ETFs/funds/bonds: 50-59, 15-16, 159, 11-13
                first_two = code[:2]
                if first_two in ("50", "51", "52", "53", "55", "56", "58", "59", "15", "16", "11", "12", "13"):
                    return False
                if code.startswith("159"):
                    return False
                return True
            df = df[df["symbol"].apply(_is_real_stock)]
        if "market_cap" in df.columns:
            top_n = 800
            df = df.nlargest(top_n, "market_cap")
    return df

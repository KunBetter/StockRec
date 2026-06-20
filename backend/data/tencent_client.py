import logging
import re
from typing import Optional

import pandas as pd
import httpx

logger = logging.getLogger(__name__)


class TencentClient:
    def __init__(self, timeout: int = 10, base_url: str = "https://qt.gtimg.cn"):
        self.timeout = timeout
        self.base_url = base_url

    BATCH_SIZE = 200

    def get_realtime_quotes(self, symbols: list[str]) -> pd.DataFrame:
        if not symbols:
            return pd.DataFrame()

        all_results = []
        for i in range(0, len(symbols), self.BATCH_SIZE):
            batch = symbols[i : i + self.BATCH_SIZE]
            batch_results = self._fetch_batch(batch)
            all_results.extend(batch_results)

        return pd.DataFrame(all_results)

    def _fetch_batch(self, symbols: list[str]) -> list[dict]:
        tencent_symbols = [s.replace("sh.", "sh").replace("sz.", "sz") for s in symbols]
        query = ",".join(tencent_symbols)
        url = f"{self.base_url}/q={query}"

        try:
            resp = httpx.get(url, timeout=self.timeout)
            resp.encoding = "gbk"
            text = resp.text

            results = []
            for line in text.strip().split("\n"):
                if not line.strip() or "=" not in line:
                    continue
                match = re.search(r'v_(\w+)="(.+)"', line)
                if not match:
                    continue
                code = match.group(1)
                values = match.group(2).split("~")
                if len(values) < 40:
                    continue

                results.append({
                    "symbol": f"sh.{code[2:]}" if code.startswith("sh") else f"sz.{code[2:]}",
                    "name": values[1],
                    "price": float(values[3]) if values[3] else None,
                    "preclose": float(values[4]) if values[4] else None,
                    "open": float(values[5]) if values[5] else None,
                    "volume": int(float(values[6])) if values[6] else 0,
                    "high": float(values[33]) if values[33] else None,
                    "low": float(values[34]) if values[34] else None,
                    "amount": float(values[37]) if values[37] else 0,
                    "pct_change": float(values[32]) if values[32] else None,
                })

            return results
        except Exception as e:
            logger.warning(f"Tencent realtime batch failed: {e}")
            return []

import logging
import re
from typing import Optional

import pandas as pd
import httpx

logger = logging.getLogger(__name__)


class SinaClient:
    def __init__(self, timeout: int = 10, base_url: str = "http://hq.sinajs.cn"):
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
        sina_symbols = [s.replace("sh.", "sh").replace("sz.", "sz") for s in symbols]
        query = ",".join(sina_symbols)
        url = f"{self.base_url}/list={query}"

        try:
            resp = httpx.get(url, timeout=self.timeout, headers={"Referer": "https://finance.sina.com.cn"})
            resp.encoding = "gbk"
            text = resp.text

            results = []
            for line in text.strip().split("\n"):
                if not line.strip():
                    continue
                match = re.search(r'hq_str_(\w+)="(.+)"', line)
                if not match:
                    continue
                code = match.group(1)
                values = match.group(2).split(",")
                if len(values) < 32:
                    continue

                results.append({
                    "symbol": f"sh.{code[2:]}" if code.startswith("sh") else f"sz.{code[2:]}",
                    "name": values[0],
                    "open": float(values[1]) if values[1] else None,
                    "preclose": float(values[2]) if values[2] else None,
                    "price": float(values[3]) if values[3] else None,
                    "high": float(values[4]) if values[4] else None,
                    "low": float(values[5]) if values[5] else None,
                    "volume": int(float(values[8])) if values[8] else 0,
                    "amount": float(values[9]) if values[9] else 0,
                })

            return results
        except Exception as e:
            logger.warning(f"Sina realtime batch failed: {e}")
            return []

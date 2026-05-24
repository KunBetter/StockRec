from abc import ABC, abstractmethod

import pandas as pd


class BaseFactor(ABC):
    name: str = ""
    category: str = ""
    depends_on: list[str] = []

    @abstractmethod
    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, category={self.category})"

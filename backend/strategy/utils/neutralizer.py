import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def neutralize_industry(
    scores: pd.Series,
    industries: pd.Series,
) -> pd.Series:
    if scores.empty or industries.empty:
        return scores

    aligned = pd.DataFrame({"score": scores, "industry": industries}).dropna()

    if len(aligned) < 5:
        return scores

    industry_means = aligned.groupby("industry")["score"].transform("mean")
    residuals = aligned["score"] - industry_means

    result = scores.copy()
    result.loc[residuals.index] = residuals
    return result


def neutralize_market_cap(
    scores: pd.Series,
    market_caps: pd.Series,
) -> pd.Series:
    if scores.empty or market_caps.empty:
        return scores

    aligned = pd.DataFrame({"score": scores, "log_cap": np.log(market_caps.replace(0, np.nan))}).dropna()

    if len(aligned) < 10:
        return scores

    X = aligned[["log_cap"]].values
    y = aligned["score"].values

    model = LinearRegression()
    model.fit(X, y)
    predicted = model.predict(X)
    residuals = y - predicted

    result = scores.copy()
    result.loc[aligned.index] = residuals
    return result

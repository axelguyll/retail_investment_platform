"""
score_markets.py
Weighted scoring model for retail real estate metros.

Weights:
  - Employment growth:     25%
  - Population growth:     20%
  - Retail vacancy trend:  25%
  - Cap rate spread:       30%
"""

import pandas as pd
import numpy as np

WEIGHTS = {
    "employment_growth": 0.25,
    "population_growth": 0.20,
    "retail_vacancy_trend": 0.25,
    "cap_rate_spread": 0.30,
}


def min_max_normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    """
    Normalize a series to [0, 1] using min-max scaling.
    If invert=True, higher raw values map to lower scores (e.g., vacancy — more negative trend is better).
    """
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    normalized = (series - min_val) / (max_val - min_val)
    if invert:
        normalized = 1 - normalized
    return normalized


def score_markets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply weighted scoring model to market DataFrame.

    Scoring logic:
    - Employment growth:    higher is better → normalize ascending
    - Population growth:    higher is better → normalize ascending
    - Retail vacancy trend: more negative is better (vacancy declining) → normalize descending (invert)
    - Cap rate spread:      higher spread vs Treasury is better → normalize ascending

    Returns DataFrame with added columns:
        score_employment, score_population, score_vacancy, score_cap_rate, total_score, rank
    """
    scored = df.copy()

    # Normalize each metric
    scored["score_employment"] = min_max_normalize(scored["employment_growth"]) * 100
    scored["score_population"] = min_max_normalize(scored["population_growth"]) * 100

    # Vacancy trend: negative means vacancy is falling (good). Invert so falling vacancy = higher score.
    scored["score_vacancy"] = min_max_normalize(scored["retail_vacancy_trend"], invert=True) * 100

    scored["score_cap_rate"] = min_max_normalize(scored["cap_rate_spread"]) * 100

    # Weighted composite score (0-100 scale)
    scored["total_score"] = (
        scored["score_employment"] * WEIGHTS["employment_growth"]
        + scored["score_population"] * WEIGHTS["population_growth"]
        + scored["score_vacancy"] * WEIGHTS["retail_vacancy_trend"]
        + scored["score_cap_rate"] * WEIGHTS["cap_rate_spread"]
    ).round(2)

    # Rank: 1 = best
    scored["rank"] = scored["total_score"].rank(ascending=False, method="min").astype(int)
    scored = scored.sort_values("rank").reset_index(drop=True)

    return scored


def get_score_breakdown(row: pd.Series) -> dict:
    """Return score contribution breakdown for a single metro row."""
    return {
        "Employment Growth (25%)": round(row["score_employment"] * WEIGHTS["employment_growth"], 2),
        "Population Growth (20%)": round(row["score_population"] * WEIGHTS["population_growth"], 2),
        "Vacancy Trend (25%)": round(row["score_vacancy"] * WEIGHTS["retail_vacancy_trend"], 2),
        "Cap Rate Spread (30%)": round(row["score_cap_rate"] * WEIGHTS["cap_rate_spread"], 2),
        "Total Score": round(row["total_score"], 2),
    }

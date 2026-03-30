"""
fetch_data.py
Fetches metro-level data from FRED, BLS, and Census APIs.
Falls back to markets.csv if any API call fails or keys are missing.
"""

import os
import requests
import pandas as pd
from pathlib import Path

# Path to fallback CSV
CSV_PATH = Path(__file__).parent / "markets.csv"

# BLS series mapping: metro -> area code (sample subset; full list uses LAUMT series)
BLS_METRO_AREAS = {
    "New York-Newark": "LAUMT363562000000003",
    "Los Angeles": "LAUMT063108000000003",
    "Chicago": "LAUMT171698000000003",
    "Dallas-Fort Worth": "LAUMT481910000000003",
    "Houston": "LAUMT482642000000003",
    "Phoenix": "LAUMT043806000000003",
    "Philadelphia": "LAUMT423798000000003",
    "San Antonio": "LAUMT484170000000003",
    "San Diego": "LAUMT064174000000003",
    "Jacksonville": "LAUMT122726000000003",
    "Austin": "LAUMT481242000000003",
    "Columbus": "LAUMT391814000000003",
    "Charlotte": "LAUMT371674000000003",
    "Indianapolis": "LAUMT182690000000003",
    "Nashville": "LAUMT473498000000003",
    "Denver": "LAUMT081974000000003",
    "Atlanta": "LAUMT131206000000003",
    "Seattle": "LAUMT534266000000003",
    "Tampa": "LAUMT124530000000003",
    "Orlando": "LAUMT123674000000003",
    "Miami": "LAUMT123310000000003",
    "Minneapolis": "LAUMT273346000000003",
    "Raleigh": "LAUMT373958000000003",
    "Portland": "LAUMT413890000000003",
    "Salt Lake City": "LAUMT494162000000003",
}

# Census population data — ACS 5-year B01003 (total population) by metro FIPS
CENSUS_METRO_FIPS = {
    "New York-Newark": "35620",
    "Los Angeles": "31080",
    "Chicago": "16980",
    "Dallas-Fort Worth": "19100",
    "Houston": "26420",
    "Phoenix": "38060",
    "Philadelphia": "37980",
    "San Antonio": "41700",
    "San Diego": "41740",
    "Jacksonville": "27260",
    "Austin": "12420",
    "Columbus": "18140",
    "Charlotte": "16740",
    "Indianapolis": "26900",
    "Nashville": "34980",
    "Denver": "19740",
    "Atlanta": "12060",
    "Seattle": "42660",
    "Tampa": "45300",
    "Orlando": "36740",
    "Miami": "33100",
    "Minneapolis": "33460",
    "Raleigh": "39580",
    "Portland": "38900",
    "Salt Lake City": "41620",
}


def fetch_treasury_rate(fred_api_key: str) -> float:
    """Fetch current 10-year Treasury rate from FRED (series DGS10)."""
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": "DGS10",
            "api_key": fred_api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
            "observation_start": "2020-01-01",
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        observations = data.get("observations", [])
        for obs in observations:
            if obs.get("value") and obs["value"] != ".":
                return float(obs["value"])
    except Exception:
        pass
    return 4.3  # fallback


def fetch_employment_data(bls_api_key: str) -> dict:
    """
    Fetch employment data for metros from BLS API v2.
    Returns dict: {metro_name: employment_growth_pct}
    """
    results = {}
    try:
        series_ids = list(BLS_METRO_AREAS.values())
        # BLS API v2 allows up to 50 series per request
        chunks = [series_ids[i:i+50] for i in range(0, len(series_ids), 50)]
        metro_names = list(BLS_METRO_AREAS.keys())

        for chunk_idx, chunk in enumerate(chunks):
            url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
            payload = {
                "seriesid": chunk,
                "startyear": "2022",
                "endyear": "2024",
                "registrationkey": bls_api_key,
            }
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            print(f"BLS response status: {data.get('status')}")
            print(f"BLS message: {data.get('message')}")
            if data.get("status") == "REQUEST_SUCCEEDED":
                for i, series in enumerate(data.get("Results", {}).get("series", [])):
                    metro_idx = chunk_idx * 50 + i
                    if metro_idx < len(metro_names):
                        metro = metro_names[metro_idx]
                        series_data = series.get("data", [])
                        if len(series_data) >= 2:
                            try:
                                latest = float(series_data[0]["value"])
                                prior = float(series_data[-1]["value"])
                                if prior > 0:
                                    growth = ((latest - prior) / prior) * 100
                                    results[metro] = round(growth, 2)
                            except (ValueError, KeyError):
                                pass
    except Exception:
        pass
    return results


def fetch_population_data(census_api_key: str) -> dict:
    """
    Fetch metro population estimates from Census ACS.
    Returns dict: {metro_name: population_growth_pct}
    """
    results = {}
    try:
        # ACS 5-year estimates — population
        url = "https://api.census.gov/data/2022/acs/acs5"
        params = {
            "get": "B01003_001E,NAME",
            "for": "metropolitan statistical area/micropolitan statistical area:*",
            "key": census_api_key,
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        rows = resp.json()

        # Build lookup by FIPS
        pop_by_fips = {}
        for row in rows[1:]:  # skip header
            try:
                pop = int(row[0])
                fips = row[2]
                pop_by_fips[fips] = pop
            except (ValueError, IndexError):
                pass

        # Also fetch 2019 for growth calc
        url2 = "https://api.census.gov/data/2019/acs/acs5"
        resp2 = requests.get(url2, params=params, timeout=15)
        resp2.raise_for_status()
        rows2 = resp2.json()
        pop_by_fips_2019 = {}
        for row in rows2[1:]:
            try:
                pop = int(row[0])
                fips = row[2]
                pop_by_fips_2019[fips] = pop
            except (ValueError, IndexError):
                pass

        for metro_name, fips in CENSUS_METRO_FIPS.items():
            pop_2022 = pop_by_fips.get(fips)
            pop_2019 = pop_by_fips_2019.get(fips)
            if pop_2022 and pop_2019 and pop_2019 > 0:
                growth = ((pop_2022 - pop_2019) / pop_2019) * 100
                results[metro_name] = round(growth, 2)
    except Exception:
        pass
    return results


def load_fallback_csv() -> pd.DataFrame:
    """Load the fallback CSV with pre-populated market data."""
    df = pd.read_csv(CSV_PATH)
    df["cap_rate_spread"] = df["cap_rate"] - df["treasury_10yr"]
    return df


def build_market_data(
    fred_api_key: str = "",
    bls_api_key: str = "",
    census_api_key: str = "",
) -> tuple[pd.DataFrame, dict]:
    """
    Attempt to build market data from live APIs.
    Falls back to CSV for any data that can't be fetched.

    Returns:
        df: DataFrame with all metro data
        source_flags: dict indicating which sources were live vs. fallback
    """
    source_flags = {
        "treasury": "fallback",
        "employment": "fallback",
        "population": "fallback",
        "vacancy_cap_rate": "csv",
    }

    # Always load CSV as base (has vacancy and cap rate data)
    df = load_fallback_csv()

    # Try FRED for treasury rate
    treasury_rate = 4.3
    if fred_api_key:
        rate = fetch_treasury_rate(fred_api_key)
        if rate:
            treasury_rate = rate
            source_flags["treasury"] = "live (FRED)"
            df["treasury_10yr"] = treasury_rate
            df["cap_rate_spread"] = df["cap_rate"] - df["treasury_10yr"]

    # Try BLS for employment growth
    if bls_api_key:
        emp_data = fetch_employment_data(bls_api_key)
        if emp_data:
            source_flags["employment"] = "live (BLS)"
            for metro, growth in emp_data.items():
                mask = df["metro"].str.contains(metro, case=False, na=False)
                if mask.any():
                    df.loc[mask, "employment_growth"] = growth

    # Try Census for population growth
    if census_api_key:
        pop_data = fetch_population_data(census_api_key)
        if pop_data:
            source_flags["population"] = "live (Census)"
            for metro, growth in pop_data.items():
                mask = df["metro"].str.contains(metro, case=False, na=False)
                if mask.any():
                    df.loc[mask, "population_growth"] = growth

    return df, source_flags

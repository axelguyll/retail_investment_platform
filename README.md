# Retail Real Estate Investment Platform

A Streamlit web app for analyzing and underwriting retail real estate investments using live government data.

**[Live Demo →](https://retailinvestmentplatform-ktmks3u783neeliwyudbbf.streamlit.app)**

---

## Features

**Market Screener**
- Scores 25+ US metros on a 0–100 scale using employment growth, population growth, vacancy trends, and cap rate spreads
- Pulls live data from FRED (Treasury rates), BLS (employment), and Census ACS (population)
- Interactive charts: top markets bar chart, score breakdown radar, employment vs. cap rate scatter

**Underwriting Tool**
- Input property details, debt terms, and exit assumptions
- Calculates IRR, equity multiple, cash-on-cash return, and DSCR
- Projects 10-year cash flows with NOI escalation
- Exports a professional PDF pro forma via ReportLab

---

## Tech Stack

- **Python** — Streamlit, Pandas, NumPy, Plotly, ReportLab
- **Data Sources** — FRED API, BLS API v2, Census ACS 5-year estimates
- **Deployment** — Streamlit Cloud

---

## Run Locally

```bash
git clone https://github.com/axelguyll/retail_investment_platform.git
cd retail_investment_platform
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
streamlit run app.py
```

Optionally add free API keys in the sidebar for live data (app works without them via CSV fallback):
- [FRED API Key](https://fred.stlouisfed.org/docs/api/api_key.html)
- [BLS API Key](https://data.bls.gov/registrationEngine/)
- [Census API Key](https://api.census.gov/data/key_signup.html)

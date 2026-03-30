"""
app.py
Retail Real Estate Investment Platform
Two-tab Streamlit application:
  Tab 1 — Market Screener (FRED/BLS/Census + weighted scoring)
  Tab 2 — Retail Underwriting Tool (IRR, DSCR, cash flows, PDF export)
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Local modules
from data.fetch_data import build_market_data
from scoring.score_markets import score_markets, get_score_breakdown, WEIGHTS
from underwriting.underwrite import DealInputs, run_underwriting
from export.pdf_export import generate_pdf

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retail Investment Platform",
    page_icon="🏬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:ital,wght@0,300;0,400;0,600;1,400&display=swap');

    * { font-family: 'Source Sans 3', -apple-system, sans-serif; }

    /* App background */
    .stApp, .main { background-color: #f1f5f9 !important; }
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }

    /* Hide Streamlit chrome */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* Navy sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a3a5c 0%, #132d47 100%) !important;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption p,
    [data-testid="stSidebar"] span:not(.st-emotion-cache-hidden) {
        color: rgba(255,255,255,0.8) !important;
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: white !important; border: none !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
    [data-testid="stSidebar"] .stTextInput input {
        background: rgba(255,255,255,0.1) !important;
        border-color: rgba(255,255,255,0.25) !important;
        color: white !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebar"] .stTextInput label { color: rgba(255,255,255,0.7) !important; }
    [data-testid="stSidebar"] strong { color: white !important; }

    /* Page header banner */
    .page-header {
        background: linear-gradient(135deg, #1a3a5c 0%, #2d6a9f 100%);
        padding: 22px 28px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(26,58,92,0.18);
    }
    .page-header h1 {
        font-family: 'Playfair Display', serif !important;
        color: white !important;
        margin: 0 !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em;
    }
    .page-header p {
        color: rgba(255,255,255,0.65);
        margin: 5px 0 0;
        font-size: 12px;
        font-weight: 300;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-bottom: 2px solid #e2e8f0;
        border-radius: 8px 8px 0 0;
        gap: 0;
        padding: 0 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #64748b !important;
        border-bottom: 3px solid transparent !important;
        margin-bottom: -2px;
        padding: 0 24px !important;
        border-radius: 0 !important;
        background: transparent !important;
        letter-spacing: 0.01em;
    }
    .stTabs [aria-selected="true"] {
        color: #1a3a5c !important;
        border-bottom: 3px solid #1a3a5c !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* Headings */
    h1 { font-family: 'Playfair Display', serif !important; color: #1a3a5c !important; }
    h2 { font-family: 'Playfair Display', serif !important; color: #1a3a5c !important; font-size: 22px !important; }
    h3 { color: #2d6a9f !important; font-size: 16px !important; font-weight: 600 !important; letter-spacing: 0.01em; }

    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-top: 3px solid #1a3a5c;
        border-radius: 8px;
        padding: 18px 16px 14px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(26,58,92,0.07);
    }
    .metric-label {
        font-size: 10px;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-family: 'Playfair Display', serif;
        font-size: 26px;
        font-weight: 700;
        color: #1a3a5c;
        line-height: 1;
        margin: 4px 0;
    }
    .metric-sub {
        font-size: 11px;
        color: #94a3b8;
        margin-top: 5px;
    }

    /* Source badges */
    .source-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"], .stFormSubmitButton > button {
        background-color: #1a3a5c !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover {
        background-color: #2d6a9f !important;
        box-shadow: 0 4px 14px rgba(26,58,92,0.3) !important;
    }

    /* Dataframe */
    .stDataFrame { border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }

    /* Form */
    [data-testid="stForm"] {
        background: white;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        padding: 20px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* HR */
    hr { border-color: #e2e8f0 !important; margin: 20px 0 !important; }

    /* Spinner */
    .stSpinner > div { border-top-color: #1a3a5c !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style='padding: 8px 0 16px;'>
            <div style='font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:rgba(255,255,255,0.45);margin-bottom:6px;'>Retail Intelligence</div>
            <div style='font-family:"Playfair Display",serif;font-size:22px;font-weight:700;color:white;line-height:1.1;'>Investment<br>Platform</div>
            <div style='height:2px;width:32px;background:rgba(255,255,255,0.25);margin-top:10px;'></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### API Keys")
    st.caption("Optional — app works without keys using CSV fallback")

    fred_key = st.text_input(
        "FRED API Key",
        value=st.secrets.get("FRED_API_KEY", os.environ.get("FRED_API_KEY", "")),
        type="password",
        help="Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html",
    )
    bls_key = st.text_input(
        "BLS API Key",
        value=st.secrets.get("BLS_API_KEY", os.environ.get("BLS_API_KEY", "")),
        type="password",
        help="Register at https://data.bls.gov/registrationEngine/",
    )
    census_key = st.text_input(
        "Census API Key",
        value=st.secrets.get("CENSUS_API_KEY", os.environ.get("CENSUS_API_KEY", "")),
        type="password",
        help="Request at https://api.census.gov/data/key_signup.html",
    )

    st.markdown("---")
    st.markdown("### Scoring Weights")
    st.caption("Weights are fixed per model spec")
    for metric, weight in WEIGHTS.items():
        label = metric.replace("_", " ").title()
        pct = int(weight * 100)
        st.markdown(
            f"<div style='margin-bottom:8px;'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
            f"<span style='font-size:12px;color:rgba(255,255,255,0.7);'>{label}</span>"
            f"<span style='font-size:12px;color:white;font-weight:600;'>{pct}%</span>"
            f"</div>"
            f"<div style='height:3px;background:rgba(255,255,255,0.15);border-radius:2px;'>"
            f"<div style='height:100%;width:{pct}%;background:rgba(255,255,255,0.5);border-radius:2px;'></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption("Data: FRED · BLS · Census ACS · CSV Fallback")


# ─── Main Content ────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class='page-header'>
        <h1>Retail Real Estate Investment Platform</h1>
        <p>Market Intelligence &amp; Underwriting Analysis</p>
    </div>
    """,
    unsafe_allow_html=True,
)
tab1, tab2 = st.tabs(["Market Screener", "Underwriting Tool"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKET SCREENER
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## Market Screener")
    st.caption("Scores 25+ US metros on employment growth, population growth, retail vacancy trend, and cap rate spread.")

    col_refresh, col_info = st.columns([1, 5])
    with col_refresh:
        load_data = st.button("Load / Refresh Data", type="primary", use_container_width=True)

    if "market_data" not in st.session_state or load_data:
        with st.spinner("Fetching market data..."):
            df_raw, source_flags = build_market_data(
                fred_api_key=fred_key,
                bls_api_key=bls_key,
                census_api_key=census_key,
            )
            df_scored = score_markets(df_raw)
            st.session_state["market_data"] = df_scored
            st.session_state["source_flags"] = source_flags

    if "market_data" not in st.session_state:
        st.info("Click 'Load / Refresh Data' to load market data.")
        st.stop()

    df_scored = st.session_state["market_data"]
    source_flags = st.session_state.get("source_flags", {})

    # Data source indicators
    with col_info:
        flag_cols = st.columns(4)
        sources = [
            ("Treasury Rate", source_flags.get("treasury", "csv")),
            ("Employment", source_flags.get("employment", "csv")),
            ("Population", source_flags.get("population", "csv")),
            ("Vacancy / Cap Rate", source_flags.get("vacancy_cap_rate", "csv")),
        ]
        for i, (label, source) in enumerate(sources):
            color = "#16a34a" if "live" in source.lower() else "#f59e0b"
            icon = "🟢" if "live" in source.lower() else "🟡"
            flag_cols[i].markdown(
                f"<div class='metric-label'>{label}</div>"
                f"<div style='font-size:12px;color:{color}'>{icon} {source}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Ranked Table ──────────────────────────────────────────────────────────
    st.markdown("### Metro Rankings")

    # Display columns
    display_cols = {
        "rank": "Rank",
        "metro": "Metro",
        "state": "State",
        "total_score": "Score",
        "employment_growth": "Employment Growth %",
        "population_growth": "Pop. Growth %",
        "retail_vacancy_trend": "Vacancy Trend (pp)",
        "cap_rate_spread": "Cap Rate Spread %",
        "cap_rate": "Cap Rate %",
    }

    df_display = df_scored[list(display_cols.keys())].rename(columns=display_cols).copy()

    # Format columns
    df_display["Score"] = df_display["Score"].map("{:.1f}".format)
    df_display["Employment Growth %"] = df_display["Employment Growth %"].map("{:.2f}%".format)
    df_display["Pop. Growth %"] = df_display["Pop. Growth %"].map("{:.2f}%".format)
    df_display["Vacancy Trend (pp)"] = df_display["Vacancy Trend (pp)"].map("{:.1f}".format)
    df_display["Cap Rate Spread %"] = df_display["Cap Rate Spread %"].map("{:.2f}%".format)
    df_display["Cap Rate %"] = df_display["Cap Rate %"].map("{:.2f}%".format)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=480,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn(width="small"),
            "Score": st.column_config.TextColumn(width="small"),
        },
    )

    st.markdown("---")

    # ── Top 10 Bar Chart ──────────────────────────────────────────────────────
    st.markdown("### Top 10 Markets by Score")
    top10 = df_scored.head(10)

    fig_bar = go.Figure()
    fig_bar.add_trace(
        go.Bar(
            x=top10["metro"],
            y=top10["total_score"],
            marker=dict(
                color=top10["total_score"],
                colorscale="Blues",
                showscale=False,
            ),
            text=top10["total_score"].map("{:.1f}".format),
            textposition="outside",
        )
    )
    fig_bar.update_layout(
        xaxis_tickangle=-30,
        yaxis_title="Composite Score (0–100)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=20, b=80, l=40, r=20),
        height=350,
        font=dict(color="#1a3a5c"),
    )
    fig_bar.update_yaxes(range=[0, 105], gridcolor="#e2e8f0")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # ── Market Drilldown ─────────────────────────────────────────────────────
    st.markdown("### Market Drilldown")
    metro_list = df_scored["metro"].tolist()
    selected_metro = st.selectbox("Select a metro for detailed analysis:", metro_list)

    row = df_scored[df_scored["metro"] == selected_metro].iloc[0]
    breakdown = get_score_breakdown(row)

    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    metrics = [
        (col_a, "Overall Score", f"{row['total_score']:.1f}", "/ 100"),
        (col_b, "Rank", f"#{int(row['rank'])}", f"of {len(df_scored)}"),
        (col_c, "Cap Rate", f"{row['cap_rate']:.2f}%", f"Spread: {row['cap_rate_spread']:.2f}%"),
        (col_d, "Emp. Growth", f"{row['employment_growth']:.2f}%", "Annual"),
        (col_e, "Pop. Growth", f"{row['population_growth']:.2f}%", "Annual"),
    ]
    for col, label, value, sub in metrics:
        col.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-label'>{label}</div>"
            f"<div class='metric-value'>{value}</div>"
            f"<div class='metric-sub'>{sub}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    drill_col1, drill_col2 = st.columns(2)

    # Score breakdown radar / bar
    with drill_col1:
        st.markdown(f"**Score Breakdown — {selected_metro}**")
        categories = list(breakdown.keys())[:-1]  # exclude Total Score
        values = [breakdown[k] for k in categories]

        fig_radar = go.Figure()
        fig_radar.add_trace(
            go.Bar(
                x=categories,
                y=values,
                marker_color=["#2d6a9f", "#16a34a", "#c8a951", "#7c3aed"],
                text=[f"{v:.1f}" for v in values],
                textposition="outside",
            )
        )
        fig_radar.update_layout(
            yaxis_title="Score Contribution",
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=20, b=60, l=40, r=10),
            height=280,
            font=dict(size=10, color="#1a3a5c"),
        )
        fig_radar.update_xaxes(tickangle=-20)
        fig_radar.update_yaxes(range=[0, 32], gridcolor="#e2e8f0")
        st.plotly_chart(fig_radar, use_container_width=True)

    # Scatter: Employment vs Cap Rate spread
    with drill_col2:
        st.markdown("**Employment Growth vs. Cap Rate Spread**")
        fig_scatter = px.scatter(
            df_scored,
            x="employment_growth",
            y="cap_rate_spread",
            size="total_score",
            color="total_score",
            hover_name="metro",
            color_continuous_scale="Blues",
            labels={
                "employment_growth": "Employment Growth (%)",
                "cap_rate_spread": "Cap Rate Spread (%)",
                "total_score": "Score",
            },
        )
        # Highlight selected metro
        sel_row = df_scored[df_scored["metro"] == selected_metro]
        fig_scatter.add_trace(
            go.Scatter(
                x=sel_row["employment_growth"],
                y=sel_row["cap_rate_spread"],
                mode="markers",
                marker=dict(color="#c8a951", size=16, symbol="star"),
                name=selected_metro,
                showlegend=True,
            )
        )
        fig_scatter.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=20, b=20, l=40, r=20),
            height=280,
            font=dict(size=10, color="#1a3a5c"),
            coloraxis_showscale=False,
        )
        fig_scatter.update_xaxes(gridcolor="#e2e8f0")
        fig_scatter.update_yaxes(gridcolor="#e2e8f0")
        st.plotly_chart(fig_scatter, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — UNDERWRITING TOOL
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Retail Property Underwriting")
    st.caption("Enter deal parameters to generate return metrics and a 10-year cash flow projection.")

    with st.form("underwriting_form"):
        st.markdown("### Property Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            property_name = st.text_input("Property Name", value="Retail Center at Main St")
        with col2:
            market = st.text_input("Market", value="Dallas-Fort Worth, TX")
        with col3:
            square_footage = st.number_input("Square Footage (SF)", value=25000, min_value=100, step=500)

        col4, col5, col6 = st.columns(3)
        with col4:
            purchase_price = st.number_input("Purchase Price ($)", value=5_000_000, min_value=1, step=50_000, format="%d")
        with col5:
            noi = st.number_input("Year 1 NOI ($)", value=325_000, min_value=1, step=5_000, format="%d")
        with col6:
            cap_rate_input = st.number_input("In-Place Cap Rate (%)", value=6.5, min_value=0.1, max_value=20.0, step=0.1)

        col7, col8 = st.columns(2)
        with col7:
            vacancy_rate = st.number_input("Vacancy Rate (%)", value=5.0, min_value=0.0, max_value=100.0, step=0.5)
        with col8:
            noi_growth = st.number_input("Annual NOI Growth Rate (%)", value=2.0, min_value=0.0, max_value=10.0, step=0.25)

        st.markdown("### Debt Terms")
        col9, col10, col11 = st.columns(3)
        with col9:
            ltv = st.number_input("LTV (%)", value=65.0, min_value=1.0, max_value=95.0, step=1.0)
        with col10:
            interest_rate = st.number_input("Interest Rate (%)", value=6.25, min_value=0.1, max_value=20.0, step=0.05)
        with col11:
            amortization = st.number_input("Amortization (Years)", value=25, min_value=1, max_value=40, step=1)

        st.markdown("### Disposition")
        col12, col13 = st.columns(2)
        with col12:
            hold_period = st.number_input("Hold Period (Years)", value=7, min_value=1, max_value=10, step=1)
        with col13:
            exit_cap = st.number_input("Exit Cap Rate (%)", value=7.0, min_value=0.1, max_value=20.0, step=0.1)

        submitted = st.form_submit_button("Run Underwriting", type="primary", use_container_width=True)

    if submitted or "uw_results" in st.session_state:
        if submitted:
            inputs = DealInputs(
                property_name=property_name,
                market=market,
                square_footage=float(square_footage),
                purchase_price=float(purchase_price),
                noi=float(noi),
                cap_rate=cap_rate_input / 100,
                vacancy_rate=vacancy_rate / 100,
                ltv=ltv / 100,
                interest_rate=interest_rate / 100,
                amortization_years=int(amortization),
                hold_period=int(hold_period),
                exit_cap_rate=exit_cap / 100,
                noi_growth_rate=noi_growth / 100,
            )
            results = run_underwriting(inputs)
            st.session_state["uw_results"] = results
            st.session_state["uw_inputs"] = inputs

        results = st.session_state["uw_results"]
        inputs = st.session_state["uw_inputs"]

        st.markdown("---")
        st.markdown("### Return Metrics")

        # Key metrics row
        irr_display = f"{results.irr * 100:.2f}%" if results.irr is not None else "N/A"
        coc_display = f"{results.cash_on_cash_year1 * 100:.2f}%"
        em_display = f"{results.equity_multiple:.2f}x"
        dscr_display = f"{results.dscr_year1:.2f}x"

        m1, m2, m3, m4 = st.columns(4)
        for col, label, value, sub in [
            (m1, "Levered IRR", irr_display, f"{inputs.hold_period}-Year Hold"),
            (m2, "Equity Multiple", em_display, "Total Distributions / Equity"),
            (m3, "Cash-on-Cash (Yr 1)", coc_display, "Year 1 Cash Flow / Equity"),
            (m4, "DSCR (Year 1)", dscr_display, "NOI / Debt Service"),
        ]:
            col.markdown(
                f"<div class='metric-card'>"
                f"<div class='metric-label'>{label}</div>"
                f"<div class='metric-value'>{value}</div>"
                f"<div class='metric-sub'>{sub}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Secondary metrics
        s1, s2, s3, s4 = st.columns(4)
        for col, label, value, sub in [
            (s1, "Equity Invested", f"${results.equity_invested:,.0f}", f"LTV: {inputs.ltv * 100:.0f}%"),
            (s2, "Loan Amount", f"${results.loan_amount:,.0f}", f"Rate: {inputs.interest_rate * 100:.2f}%"),
            (s3, "Annual Debt Service", f"${results.annual_debt_service:,.0f}", f"Monthly: ${results.monthly_payment:,.0f}"),
            (s4, "Net Sale Proceeds", f"${results.net_sale_proceeds:,.0f}", f"Exit Cap: {inputs.exit_cap_rate * 100:.1f}%"),
        ]:
            col.markdown(
                f"<div class='metric-card'>"
                f"<div class='metric-label'>{label}</div>"
                f"<div class='metric-value' style='font-size:20px'>{value}</div>"
                f"<div class='metric-sub'>{sub}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")

        # ── Cash Flow Table ─────────────────────────────────────────────────
        st.markdown("### 10-Year Cash Flow Projection")
        cf = results.cash_flow_table

        # Styled dataframe
        def style_cf_table(df):
            def highlight_exit(row):
                if row["Year"] == inputs.hold_period:
                    return ["background-color: #e8f0f8; font-weight: bold"] * len(row)
                return [""] * len(row)

            return df.style.apply(highlight_exit, axis=1).format(
                {
                    "NOI": "${:,.0f}",
                    "Debt Service": "${:,.0f}",
                    "Cash Flow (Ops)": "${:,.0f}",
                    "Net Sale Proceeds": "${:,.0f}",
                    "Total Cash Flow": "${:,.0f}",
                    "Cumulative Cash Flow": "${:,.0f}",
                    "Loan Balance": "${:,.0f}",
                }
            )

        st.dataframe(style_cf_table(cf), use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── Charts ──────────────────────────────────────────────────────────
        st.markdown("### Visual Analysis")
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**NOI & Cash Flow by Year**")
            fig_cf = go.Figure()
            fig_cf.add_trace(
                go.Bar(
                    name="NOI",
                    x=cf["Year"],
                    y=cf["NOI"],
                    marker_color="#2d6a9f",
                )
            )
            fig_cf.add_trace(
                go.Bar(
                    name="Cash Flow (Ops)",
                    x=cf["Year"],
                    y=cf["Cash Flow (Ops)"],
                    marker_color="#16a34a",
                )
            )
            fig_cf.update_layout(
                barmode="group",
                xaxis_title="Year",
                yaxis_title="Amount ($)",
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=10, b=40, l=60, r=10),
                height=300,
                legend=dict(orientation="h", y=1.1),
                font=dict(size=10),
            )
            fig_cf.update_yaxes(gridcolor="#e2e8f0", tickformat="$,.0f")
            fig_cf.update_xaxes(tickmode="array", tickvals=cf["Year"].tolist())
            st.plotly_chart(fig_cf, use_container_width=True)

        with chart_col2:
            st.markdown("**Cumulative Cash Flow**")
            fig_cum = go.Figure()
            fig_cum.add_trace(
                go.Scatter(
                    x=cf["Year"],
                    y=cf["Cumulative Cash Flow"],
                    mode="lines+markers",
                    line=dict(color="#2d6a9f", width=2.5),
                    marker=dict(size=8, color="#2d6a9f"),
                    fill="tozeroy",
                    fillcolor="rgba(45, 106, 159, 0.12)",
                )
            )
            # Add zero line
            fig_cum.add_hline(y=0, line_dash="dot", line_color="gray", line_width=1)
            fig_cum.update_layout(
                xaxis_title="Year",
                yaxis_title="Cumulative Cash Flow ($)",
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(t=10, b=40, l=60, r=10),
                height=300,
                font=dict(size=10),
            )
            fig_cum.update_yaxes(gridcolor="#e2e8f0", tickformat="$,.0f")
            fig_cum.update_xaxes(tickmode="array", tickvals=cf["Year"].tolist())
            st.plotly_chart(fig_cum, use_container_width=True)

        # Loan amortization chart
        st.markdown("**Loan Balance Over Hold Period**")
        fig_loan = go.Figure()
        fig_loan.add_trace(
            go.Scatter(
                x=cf["Year"],
                y=cf["Loan Balance"],
                mode="lines+markers",
                line=dict(color="#c8a951", width=2.5),
                marker=dict(size=8),
                name="Loan Balance",
                fill="tozeroy",
                fillcolor="rgba(200, 169, 81, 0.15)",
            )
        )
        fig_loan.update_layout(
            xaxis_title="Year",
            yaxis_title="Remaining Loan Balance ($)",
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(t=10, b=40, l=60, r=10),
            height=250,
            font=dict(size=10),
        )
        fig_loan.update_yaxes(gridcolor="#e2e8f0", tickformat="$,.0f")
        fig_loan.update_xaxes(tickmode="array", tickvals=cf["Year"].tolist())
        st.plotly_chart(fig_loan, use_container_width=True)

        st.markdown("---")

        # ── PDF Export ──────────────────────────────────────────────────────
        st.markdown("### Export Pro Forma")
        pdf_col, _ = st.columns([2, 4])
        with pdf_col:
            if st.button("Export PDF", type="primary", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    pdf_bytes = generate_pdf(inputs, results)
                    filename = f"{inputs.property_name.replace(' ', '_').replace('/', '-')}_ProForma.pdf"
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                st.success("PDF generated successfully!")

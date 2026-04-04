# Demo Readiness Design — Sand Capital Presentation
**Date:** 2026-04-03  
**Presentation:** April 13, 2026  
**Audience:** Sand Capital / Sandor Development — senior CRE investment professionals  
**Context:** Internship candidate demo for AI & Automation role; platform is the work sample

---

## Background

The Retail Real Estate Investment Platform is a two-tab Streamlit app:
- **Market Screener** — scores 25+ US metros using live FRED/BLS/Census data
- **Underwriting Tool** — IRR, DSCR, equity multiple, 10-year cash flows, PDF export

Sand Capital is one of the largest privately-held retail developers in the US (8M+ sq ft, 25 states). The platform's scope maps directly to their operation. The demo audience will evaluate both the platform and the candidate's ability to bring AI/automation to a traditional CRE firm.

Three features are added to elevate the platform from functional to demo-worthy.

---

## Feature 1: Interactive Market Heat Map

### What it does
A choropleth map of the United States added as a new sub-view inside the Market Screener tab. States are colored on a navy-to-light-blue scale based on their highest-scoring metro. Clicking a state opens a side panel listing all metros in that state with scores and ranks. Clicking a metro drills into its score breakdown and provides a direct link into the Underwriting Tool.

### Architecture
- **Location:** Tab 1 (Market Screener), new "Market Map" toggle alongside existing Rankings Table and Charts views
- **Data:** Uses the already-scored `df_scored` DataFrame from `score_markets()` — no new data sources
- **State aggregation:** Each state is colored by the `max(total_score)` of its metros in the dataset
- **Library:** `plotly.choropleth` with `locationmode='USA-states'`
- **Color scale:** `[[0, '#dbeafe'], [0.4, '#60a5fa'], [0.65, '#2d6a9f'], [0.85, '#1e40af'], [1.0, '#1a3a5c']]` — matches platform Navy theme
- **Interactivity:** `st.plotly_chart(..., on_select='rerun')` captures click events; selected state stored in `st.session_state`

### Side panel behavior
1. Click state → show all metros in that state, each as a card with score + rank
2. Click metro card → show score breakdown (employment, population, vacancy, cap rate spread) as horizontal bars + cap rate vs. 10-yr Treasury
3. "Underwrite a Deal in [Metro] →" button sets `st.session_state['selected_market']` and switches to Tab 2

### Demo flow this enables
Map → click Texas → see Austin ranked #1 → click Austin → see score breakdown → "Underwrite Here" → Underwriting tab pre-filled with Dallas-Fort Worth as market label → run deal → sensitivity table populates → generate memo

---

## Feature 2: Sensitivity Analysis Table

### What it does
An IRR sensitivity grid displayed below the 10-year cash flow projection in the Underwriting Tool. Shows how Levered IRR changes across a matrix of exit cap rates (columns) and hold periods (rows). Color-coded green → yellow → red. The current deal's inputs are highlighted with a border.

### Architecture
- **Location:** Tab 2 (Underwriting Tool), after the cash flow projection, before the PDF export button
- **Axes:**
  - Rows: Hold period — 1 through 10 years
  - Columns: Exit cap rate — current exit cap ± 150 bps in 25 bp increments (13 columns)
- **Calculation:** For each cell, re-run `run_underwriting()` with modified `hold_period` and `exit_cap_rate`; extract `results.irr`. Uses existing underwriting engine — no new math.
- **Performance:** 10 × 13 = 130 cells. Each call is pure Python/numpy, no I/O. Runs in under 1 second total; wrap in `st.spinner`.
- **Highlighting:** Current inputs cell gets `border: 2px solid #1a3a5c` via Pandas Styler
- **Color thresholds:** IRR ≥ 15% → green (`#dcfce7`), 10–15% → yellow (`#fefce8`), 5–10% → orange (`#fff7ed`), < 5% → red (`#fef2f2`)

### Why it matters for the demo
CRE professionals use sensitivity tables to stress-test deals. Showing one instantly signals institutional-grade tooling. It also makes the demo interactive — they can ask "what if cap rates expand?" and you point to the table.

---

## Feature 3: AI-Generated Investment Memo

### What it does
A "Generate Investment Memo" button in the Underwriting Tool. After a deal is run, one click sends the deal inputs and results to the Claude API and returns a formatted 1-page investment memo displayed in the app. The memo can also be downloaded as a PDF.

### Architecture
- **Location:** Tab 2, alongside the existing "Export PDF" button
- **API:** `anthropic` Python SDK, `claude-sonnet-4-6` model
- **API key:** Added as a new optional field in the sidebar (`ANTHROPIC_API_KEY`), consistent with existing FRED/BLS/Census key pattern. Reads from `st.secrets` or env var first.
- **Prompt design:** System prompt establishes persona as a senior CRE investment analyst. User message contains structured deal data (property name, market, purchase price, NOI, cap rate, debt terms, IRR, DSCR, equity multiple, cash-on-cash, hold period, exit cap). Instructs Claude to produce a memo with fixed sections.

### Memo output sections
1. **Property Overview** — name, market, size, purchase price, in-place cap rate
2. **Market Context** — 1–2 sentences on why this market scores well (drawn from screener data if available, otherwise from deal inputs)
3. **Investment Structure** — equity, debt, LTV, interest rate, hold period
4. **Return Profile** — IRR, equity multiple, cash-on-cash, DSCR; qualitative read on strength
5. **Key Risks** — cap rate expansion, NOI underperformance, exit timing
6. **Recommendation** — proceed / proceed with conditions / pass, with one-sentence rationale

### Display
- Rendered as styled markdown in a Streamlit `st.container()` with the platform's card styling
- "Download Memo PDF" button generates a second PDF via ReportLab (separate from the pro forma PDF)
- Streamed output using `client.messages.stream()` so text appears progressively — more impressive live

### Error handling
- If no API key: button is disabled with caption "Add Anthropic API key in sidebar to enable"
- If API call fails: show `st.error()` with message, do not crash

---

## UI Polish

- Tighten tab panel padding for better use of horizontal space at wide layouts
- Ensure Market Map tab renders cleanly at standard laptop resolution (1280×800)
- Add section dividers in the Underwriting tab to visually separate: Inputs → Metrics → Cash Flow → Sensitivity → Memo → Export
- Sidebar: add Anthropic API key field below Census key, same styling

---

## What This Achieves for the Demo

| Moment | Feature |
|---|---|
| "Here's how we screen markets across your 25-state footprint" | Heat Map |
| "Click Texas — you can see Austin leads, let's underwrite something there" | Map → Underwriting handoff |
| "Here's how the IRR changes if cap rates expand 50bps at exit" | Sensitivity Table |
| "And here's the investment memo the platform just drafted" | AI Memo |
| "You can download the full pro forma or the memo as a PDF" | Existing + new PDF export |

The demo narrative: data pipeline → market ranking → deal underwriting → stress testing → AI-drafted memo. Each step flows into the next. The AI memo is the closing moment that directly answers the "AI & Automation" role requirement.

---

## Out of Scope

- New data sources beyond FRED/BLS/Census/CSV
- Portfolio-level analysis or multi-deal comparison
- User authentication or saved deals
- Mobile responsiveness
- Tenant or property database integration

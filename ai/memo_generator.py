"""
memo_generator.py
Generates an investment memo via the Claude API.

Usage:
    system_prompt, user_prompt = build_memo_prompt(inputs, results)
    # Pass to Anthropic client for streaming or non-streaming call.
"""

from underwriting.underwrite import DealInputs, UnderwritingResults


def build_memo_prompt(inputs: DealInputs, results: UnderwritingResults) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the Claude API memo generation call.
    Keeping prompt construction separate from the API call makes it testable
    without requiring an API key.
    """
    irr_str = f"{results.irr * 100:.2f}%" if results.irr is not None else "N/A"
    coc_str = f"{results.cash_on_cash_year1 * 100:.2f}%"

    system_prompt = (
        "You are a senior commercial real estate investment analyst at a private equity firm "
        "specializing in retail property acquisitions. You write clear, professional, and "
        "concise investment memos. Your memos are fact-based, balanced, and suitable for "
        "presentation to investment committee principals. Do not use filler phrases or "
        "excessive hedging. Write in plain English — no jargon without explanation."
    )

    user_prompt = f"""Write a one-page investment memo for the following retail property acquisition.

## Deal Data

**Property:** {inputs.property_name}
**Market:** {inputs.market}
**Size:** {inputs.square_footage:,.0f} SF
**Purchase Price:** ${inputs.purchase_price:,.0f} (${results.price_per_sf:.2f}/SF)
**In-Place Cap Rate:** {inputs.cap_rate * 100:.2f}%
**Year 1 NOI:** ${inputs.noi:,.0f} (${results.noi_per_sf:.2f}/SF)
**Vacancy Assumption:** {inputs.vacancy_rate * 100:.1f}%
**NOI Growth Rate:** {inputs.noi_growth_rate * 100:.1f}% per year

**Debt Structure:**
- LTV: {inputs.ltv * 100:.0f}%
- Loan Amount: ${results.loan_amount:,.0f}
- Interest Rate: {inputs.interest_rate * 100:.2f}%
- Amortization: {inputs.amortization_years} years
- Annual Debt Service: ${results.annual_debt_service:,.0f}

**Return Profile:**
- Hold Period: {inputs.hold_period} years
- Exit Cap Rate: {inputs.exit_cap_rate * 100:.2f}%
- Levered IRR: {irr_str}
- Equity Multiple: {results.equity_multiple:.2f}x
- Cash-on-Cash (Year 1): {coc_str}
- DSCR (Year 1): {results.dscr_year1:.2f}x
- Net Sale Proceeds: ${results.net_sale_proceeds:,.0f}
- Equity Invested: ${results.equity_invested:,.0f}

## Memo Format

Write the memo with exactly these six sections in order. Use markdown headers (##).

## Property Overview
One short paragraph: property type, location, size, purchase price, in-place cap rate. No fluff.

## Market Context
Two to three sentences: why this market is compelling for retail real estate investment. Reference employment growth, population trends, or cap rate spreads relative to Treasuries if relevant. Be specific.

## Investment Structure
One short paragraph covering equity invested, loan terms, hold period, and exit assumption.

## Return Profile
Bullet points for IRR, equity multiple, cash-on-cash, and DSCR. Follow each metric with one sentence of qualitative interpretation. Mention whether the DSCR provides adequate debt coverage cushion.

## Key Risks
Three to five bullet points. Be direct. Examples: cap rate expansion at exit, NOI underperformance vs. projection, tenant rollover risk, interest rate sensitivity, market liquidity.

## Recommendation
One sentence: Proceed / Proceed with conditions / Pass — and a one-sentence rationale tied to the return profile and key risk.

Write the memo now. Do not include any preamble before the first section header."""

    return system_prompt, user_prompt


def generate_memo_streaming(api_key: str, inputs: DealInputs, results: UnderwritingResults):
    """
    Generator that yields text chunks from the Claude API (streaming).
    Caller is responsible for rendering chunks.

    Usage in Streamlit:
        memo_text = ""
        memo_container = st.empty()
        for chunk in generate_memo_streaming(api_key, inputs, results):
            memo_text += chunk
            memo_container.markdown(memo_text)
    """
    import anthropic

    system_prompt, user_prompt = build_memo_prompt(inputs, results)
    client = anthropic.Anthropic(api_key=api_key)

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text

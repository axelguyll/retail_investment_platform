"""
underwrite.py
Core financial calculations for retail property underwriting.

All formulas are mathematically rigorous:
  - IRR via numpy_financial.irr()
  - DSCR = NOI / Annual Debt Service
  - Cash-on-Cash = Year 1 Cash Flow / Equity Invested
  - Equity Multiple = Total Distributions / Equity Invested
  - Annual Debt Service via standard mortgage amortization formula
"""

import numpy as np
import numpy_financial as npf
import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class DealInputs:
    property_name: str
    market: str
    square_footage: float
    purchase_price: float
    noi: float                  # Year 1 NOI
    cap_rate: float             # In-place cap rate (as decimal, e.g. 0.065)
    vacancy_rate: float         # As decimal (e.g. 0.05)
    ltv: float                  # Loan-to-value ratio (as decimal, e.g. 0.65)
    interest_rate: float        # Annual interest rate (as decimal, e.g. 0.055)
    amortization_years: int     # Amortization period in years
    hold_period: int            # Hold period in years (1-10)
    exit_cap_rate: float        # Exit cap rate (as decimal)
    noi_growth_rate: float = 0.02   # Annual NOI growth rate (default 2%)


@dataclass
class UnderwritingResults:
    # Deal structure
    loan_amount: float
    equity_invested: float
    loan_to_value: float

    # Annual debt service
    annual_debt_service: float
    monthly_payment: float

    # Return metrics
    irr: Optional[float]
    equity_multiple: float
    cash_on_cash_year1: float
    dscr_year1: float

    # Year 1 metrics
    noi_year1: float
    cash_flow_year1: float
    net_sale_proceeds: float

    # Projections
    cash_flow_table: pd.DataFrame

    # Per SF
    price_per_sf: float
    noi_per_sf: float


def calculate_annual_debt_service(
    loan_amount: float,
    annual_interest_rate: float,
    amortization_years: int,
) -> tuple[float, float]:
    """
    Calculate annual debt service using standard mortgage amortization formula.

    Monthly payment = P * [r(1+r)^n] / [(1+r)^n - 1]
    where:
        P = principal (loan amount)
        r = monthly interest rate
        n = total number of payments

    Returns (annual_debt_service, monthly_payment)
    """
    if annual_interest_rate <= 0 or amortization_years <= 0 or loan_amount <= 0:
        return 0.0, 0.0

    monthly_rate = annual_interest_rate / 12
    n_payments = amortization_years * 12

    # Standard mortgage formula
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** n_payments) / (
        (1 + monthly_rate) ** n_payments - 1
    )
    annual_debt_service = monthly_payment * 12
    return round(annual_debt_service, 2), round(monthly_payment, 2)


def calculate_remaining_loan_balance(
    loan_amount: float,
    annual_interest_rate: float,
    amortization_years: int,
    years_elapsed: int,
) -> float:
    """
    Calculate remaining loan balance after `years_elapsed` years
    using the standard amortization formula.

    Remaining balance = P * [(1+r)^n - (1+r)^k] / [(1+r)^n - 1]
    where k = payments made, n = total payments
    """
    if annual_interest_rate <= 0 or loan_amount <= 0:
        return loan_amount

    monthly_rate = annual_interest_rate / 12
    n = amortization_years * 12
    k = years_elapsed * 12

    if n == k:
        return 0.0

    remaining = loan_amount * (
        ((1 + monthly_rate) ** n - (1 + monthly_rate) ** k)
        / ((1 + monthly_rate) ** n - 1)
    )
    return max(round(remaining, 2), 0.0)


def project_cash_flows(inputs: DealInputs) -> pd.DataFrame:
    """
    Build a year-by-year cash flow projection table.

    For each year:
        - NOI escalates at noi_growth_rate
        - Cash flow before tax = NOI - Annual Debt Service
        - In the final year, add net sale proceeds

    Returns DataFrame with columns:
        Year, NOI, Annual Debt Service, Cash Flow, Cumulative Cash Flow,
        Loan Balance, Net Sale Proceeds (final year only)
    """
    loan_amount = inputs.purchase_price * inputs.ltv
    equity_invested = inputs.purchase_price - loan_amount

    annual_ds, _ = calculate_annual_debt_service(
        loan_amount, inputs.interest_rate, inputs.amortization_years
    )

    rows = []
    cumulative_cf = 0.0

    for year in range(1, inputs.hold_period + 1):
        # NOI grows at specified annual rate
        noi_year = inputs.noi * (1 + inputs.noi_growth_rate) ** (year - 1)

        # Cash flow from operations
        cf_operations = noi_year - annual_ds

        # Remaining loan balance at end of this year
        loan_balance = calculate_remaining_loan_balance(
            loan_amount, inputs.interest_rate, inputs.amortization_years, year
        )

        # Net sale proceeds (only in exit year)
        net_sale_proceeds = 0.0
        total_cf = cf_operations

        if year == inputs.hold_period:
            # Exit value = NOI at exit year / exit cap rate
            exit_noi = noi_year
            exit_value = exit_noi / inputs.exit_cap_rate
            net_sale_proceeds = exit_value - loan_balance
            total_cf = cf_operations + net_sale_proceeds

        cumulative_cf += total_cf

        rows.append(
            {
                "Year": year,
                "NOI": round(noi_year, 0),
                "Debt Service": round(annual_ds, 0),
                "Cash Flow (Ops)": round(cf_operations, 0),
                "Net Sale Proceeds": round(net_sale_proceeds, 0),
                "Total Cash Flow": round(total_cf, 0),
                "Cumulative Cash Flow": round(cumulative_cf, 0),
                "Loan Balance": round(loan_balance, 0),
            }
        )

    return pd.DataFrame(rows)


def calculate_irr(inputs: DealInputs, cf_table: pd.DataFrame) -> Optional[float]:
    """
    Calculate IRR using numpy_financial.irr().

    Cash flow array:
        Year 0: -equity_invested
        Years 1 to N: annual Total Cash Flow (ops + sale in exit year)
    """
    loan_amount = inputs.purchase_price * inputs.ltv
    equity_invested = inputs.purchase_price - loan_amount

    cf_array = [-equity_invested] + list(cf_table["Total Cash Flow"])

    try:
        irr = npf.irr(cf_array)
        if np.isnan(irr) or np.isinf(irr):
            return None
        return round(float(irr), 6)
    except Exception:
        return None


def run_underwriting(inputs: DealInputs) -> UnderwritingResults:
    """
    Run the full underwriting model and return results.
    """
    loan_amount = round(inputs.purchase_price * inputs.ltv, 2)
    equity_invested = round(inputs.purchase_price - loan_amount, 2)

    annual_ds, monthly_payment = calculate_annual_debt_service(
        loan_amount, inputs.interest_rate, inputs.amortization_years
    )

    # Build cash flow table
    cf_table = project_cash_flows(inputs)

    # IRR
    irr = calculate_irr(inputs, cf_table)

    # Year 1 metrics
    noi_year1 = inputs.noi
    cf_year1 = float(cf_table.loc[cf_table["Year"] == 1, "Cash Flow (Ops)"].iloc[0])

    # DSCR Year 1
    dscr_year1 = round(noi_year1 / annual_ds, 3) if annual_ds > 0 else 0.0

    # Cash-on-cash Year 1
    coc_year1 = round(cf_year1 / equity_invested, 6) if equity_invested > 0 else 0.0

    # Equity multiple = total distributions (all cash flows incl. exit) / equity
    total_distributions = float(cf_table["Total Cash Flow"].sum())
    equity_multiple = round(total_distributions / equity_invested, 3) if equity_invested > 0 else 0.0

    # Net sale proceeds (from exit year row)
    net_sale_proceeds = float(
        cf_table.loc[cf_table["Year"] == inputs.hold_period, "Net Sale Proceeds"].iloc[0]
    )

    return UnderwritingResults(
        loan_amount=loan_amount,
        equity_invested=equity_invested,
        loan_to_value=inputs.ltv,
        annual_debt_service=annual_ds,
        monthly_payment=monthly_payment,
        irr=irr,
        equity_multiple=equity_multiple,
        cash_on_cash_year1=coc_year1,
        dscr_year1=dscr_year1,
        noi_year1=noi_year1,
        cash_flow_year1=cf_year1,
        net_sale_proceeds=net_sale_proceeds,
        cash_flow_table=cf_table,
        price_per_sf=round(inputs.purchase_price / inputs.square_footage, 2) if inputs.square_footage > 0 else 0.0,
        noi_per_sf=round(inputs.noi / inputs.square_footage, 2) if inputs.square_footage > 0 else 0.0,
    )

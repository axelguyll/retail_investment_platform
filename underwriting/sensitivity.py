"""
sensitivity.py
Builds an IRR sensitivity grid for the underwriting tool.

Axes:
  - Rows:    Hold period (1–10 years)
  - Columns: Exit cap rate (base ± 150 bps in 25 bp steps → 13 values)
"""

import numpy as np
import pandas as pd
from dataclasses import replace
from underwriting.underwrite import DealInputs, run_underwriting


def build_sensitivity_grid(inputs: DealInputs) -> pd.DataFrame:
    """
    Return a DataFrame of Levered IRR values.

    Index:   hold periods 1..10 (int)
    Columns: exit cap rates as decimals, base ± 150bps in 25bp steps

    Cell value: IRR as float (e.g. 0.142 = 14.2%), or None if IRR undefined.
    """
    base_cap = inputs.exit_cap_rate
    # 13 steps: -150bps, -125, ..., 0, ..., +125, +150
    cap_offsets = [i * 0.0025 for i in range(-6, 7)]
    exit_caps = [round(base_cap + offset, 6) for offset in cap_offsets]
    hold_periods = list(range(1, 11))

    data = {}
    for cap in exit_caps:
        col = []
        for hold in hold_periods:
            modified = replace(inputs, exit_cap_rate=cap, hold_period=hold)
            try:
                results = run_underwriting(modified)
                col.append(results.irr)
            except Exception:
                col.append(None)
        data[cap] = col

    df = pd.DataFrame(data, index=hold_periods)
    return df


def style_sensitivity_grid(df: pd.DataFrame, current_hold: int, current_exit_cap: float) -> object:
    """
    Apply color coding and formatting to the sensitivity grid for display.

    Color thresholds:
      >= 15%  → green
      10–15%  → yellow
      5–10%   → orange
      < 5%    → red
      None    → gray

    Current inputs cell gets a bold border highlight via CSS outline.
    """
    def color_cell(val):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "background-color: #f1f5f9; color: #94a3b8"
        if val >= 0.15:
            return "background-color: #dcfce7; color: #15803d; font-weight: 600"
        if val >= 0.10:
            return "background-color: #fefce8; color: #854d0e; font-weight: 600"
        if val >= 0.05:
            return "background-color: #fff7ed; color: #c2410c; font-weight: 600"
        return "background-color: #fef2f2; color: #b91c1c; font-weight: 600"

    def highlight_row(row):
        styles = []
        for col in df.columns:
            base_style = color_cell(row[col])
            # Highlight the current deal's exact cell
            if row.name == current_hold and abs(col - current_exit_cap) < 0.0001:
                base_style += "; outline: 2px solid #1a3a5c; outline-offset: -2px"
            styles.append(base_style)
        return styles

    # Format IRR values as percentages
    formatted = df.map(
        lambda v: f"{v * 100:.1f}%" if v is not None and not (isinstance(v, float) and np.isnan(v)) else "N/A"
    )

    # Rename columns to show bps offset from base
    col_labels = {
        c: f"{(c - current_exit_cap) * 10000:+.0f}bp" if abs(c - current_exit_cap) > 0.00001 else "Base"
        for c in df.columns
    }
    formatted = formatted.rename(columns=col_labels)

    styled = formatted.style.apply(
        lambda row: highlight_row(df.loc[row.name]),
        axis=1,
    )
    return styled

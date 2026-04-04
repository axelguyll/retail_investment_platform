"""
market_map.py
Builds the US choropleth heat map for the Market Screener.
"""

import pandas as pd
import plotly.graph_objects as go


# Navy color scale matching platform theme
CHOROPLETH_COLORSCALE = [
    [0.0,  "#dbeafe"],
    [0.35, "#60a5fa"],
    [0.60, "#2d6a9f"],
    [0.80, "#1e40af"],
    [1.0,  "#1a3a5c"],
]


def aggregate_to_states(df: pd.DataFrame) -> dict:
    """
    Aggregate metro-level scored DataFrame to state level.

    Returns a dict keyed by state code:
      {
        "TX": {
          "top_score": 88.0,
          "top_metro": "Austin",
          "metros": [
            {"metro": "Austin", "total_score": 88.0, "rank": 1, ...},
            ...
          ]
        },
        ...
      }
    """
    state_data = {}

    for _, row in df.iterrows():
        state = row["state"]
        if state not in state_data:
            state_data[state] = {"top_score": -1, "top_metro": "", "metros": []}

        metro_entry = row.to_dict()
        state_data[state]["metros"].append(metro_entry)

        if row["total_score"] > state_data[state]["top_score"]:
            state_data[state]["top_score"] = row["total_score"]
            state_data[state]["top_metro"] = row["metro"]

    # Sort metros within each state descending by score
    for state in state_data:
        state_data[state]["metros"].sort(key=lambda x: x["total_score"], reverse=True)

    return state_data


def build_choropleth_figure(state_data: dict) -> go.Figure:
    """
    Build a Plotly choropleth figure from aggregated state data.
    States are colored by their top metro's total_score (0-100 scale).
    """
    states = list(state_data.keys())
    scores = [state_data[s]["top_score"] for s in states]
    hover_texts = [
        f"<b>{s}</b><br>Top: {state_data[s]['top_metro']}<br>Score: {state_data[s]['top_score']:.1f}"
        for s in states
    ]

    fig = go.Figure(
        data=go.Choropleth(
            locationmode="USA-states",
            locations=states,
            z=scores,
            text=hover_texts,
            hovertemplate="%{text}<extra></extra>",
            colorscale=CHOROPLETH_COLORSCALE,
            zmin=0,
            zmax=100,
            marker_line_color="white",
            marker_line_width=1.5,
            showscale=False,
        )
    )

    fig.update_layout(
        geo=dict(
            scope="usa",
            showlakes=False,
            showland=True,
            landcolor="#e2e8f0",
            bgcolor="#f8fafc",
            showframe=False,
            showcoastlines=False,
        ),
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    return fig

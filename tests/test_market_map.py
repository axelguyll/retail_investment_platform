import pandas as pd
import pytest
from map.market_map import aggregate_to_states, build_choropleth_figure


@pytest.fixture
def sample_df():
    return pd.DataFrame([
        {"metro": "Austin", "state": "TX", "total_score": 88.0, "rank": 1,
         "employment_growth": 5.2, "population_growth": 3.1,
         "retail_vacancy_trend": -1.4, "cap_rate_spread": 2.6, "cap_rate": 6.9},
        {"metro": "Dallas-Fort Worth", "state": "TX", "total_score": 72.0, "rank": 4,
         "employment_growth": 3.8, "population_growth": 2.1,
         "retail_vacancy_trend": -0.8, "cap_rate_spread": 2.0, "cap_rate": 6.3},
        {"metro": "Phoenix", "state": "AZ", "total_score": 84.0, "rank": 2,
         "employment_growth": 4.1, "population_growth": 2.4,
         "retail_vacancy_trend": -1.0, "cap_rate_spread": 2.5, "cap_rate": 6.8},
    ])


def test_aggregate_to_states_picks_highest_score(sample_df):
    result = aggregate_to_states(sample_df)
    assert result["TX"]["top_score"] == 88.0
    assert result["TX"]["top_metro"] == "Austin"
    assert result["AZ"]["top_score"] == 84.0


def test_aggregate_to_states_includes_all_metros(sample_df):
    result = aggregate_to_states(sample_df)
    assert len(result["TX"]["metros"]) == 2
    # metros sorted descending by score
    assert result["TX"]["metros"][0]["metro"] == "Austin"
    assert result["TX"]["metros"][1]["metro"] == "Dallas-Fort Worth"


def test_build_choropleth_figure_returns_plotly_figure(sample_df):
    import plotly.graph_objects as go
    state_data = aggregate_to_states(sample_df)
    fig = build_choropleth_figure(state_data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "choropleth"

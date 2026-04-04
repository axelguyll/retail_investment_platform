import pytest
from underwriting.underwrite import DealInputs
from underwriting.sensitivity import build_sensitivity_grid


@pytest.fixture
def base_inputs():
    return DealInputs(
        property_name="Test Property",
        market="Dallas-Fort Worth, TX",
        square_footage=25000.0,
        purchase_price=5_000_000.0,
        noi=325_000.0,
        cap_rate=0.065,
        vacancy_rate=0.05,
        ltv=0.65,
        interest_rate=0.0625,
        amortization_years=25,
        hold_period=7,
        exit_cap_rate=0.07,
        noi_growth_rate=0.02,
    )


def test_sensitivity_grid_shape(base_inputs):
    grid = build_sensitivity_grid(base_inputs)
    # 10 hold periods (1–10), 13 exit cap columns (base ± 150bps in 25bp steps)
    assert grid.shape == (10, 13)


def test_sensitivity_grid_index(base_inputs):
    grid = build_sensitivity_grid(base_inputs)
    assert list(grid.index) == list(range(1, 11))  # hold periods 1..10


def test_sensitivity_grid_current_cell_not_none(base_inputs):
    grid = build_sensitivity_grid(base_inputs)
    # Middle column (index 6) is always the base exit cap rate
    val = grid.iloc[base_inputs.hold_period - 1, 6]
    assert val is not None
    assert isinstance(val, float)


def test_sensitivity_grid_higher_exit_cap_lowers_irr(base_inputs):
    grid = build_sensitivity_grid(base_inputs)
    caps = sorted(grid.columns)
    # For same hold period, higher exit cap → lower IRR
    row = base_inputs.hold_period
    low_cap_irr = grid.loc[row, caps[0]]
    high_cap_irr = grid.loc[row, caps[-1]]
    assert low_cap_irr > high_cap_irr

import pytest
from underwriting.underwrite import DealInputs
from ai.memo_generator import build_memo_prompt


@pytest.fixture
def sample_inputs():
    return DealInputs(
        property_name="Riverside Retail Center",
        market="Austin, TX",
        square_footage=20000.0,
        purchase_price=4_000_000.0,
        noi=280_000.0,
        cap_rate=0.07,
        vacancy_rate=0.05,
        ltv=0.65,
        interest_rate=0.0625,
        amortization_years=25,
        hold_period=7,
        exit_cap_rate=0.075,
        noi_growth_rate=0.02,
    )


@pytest.fixture
def sample_results(sample_inputs):
    from underwriting.underwrite import run_underwriting
    return run_underwriting(sample_inputs)


def test_build_memo_prompt_contains_property_name(sample_inputs, sample_results):
    system, user = build_memo_prompt(sample_inputs, sample_results)
    assert "Riverside Retail Center" in user


def test_build_memo_prompt_contains_market(sample_inputs, sample_results):
    system, user = build_memo_prompt(sample_inputs, sample_results)
    assert "Austin" in user


def test_build_memo_prompt_contains_irr(sample_inputs, sample_results):
    system, user = build_memo_prompt(sample_inputs, sample_results)
    assert "IRR" in user


def test_build_memo_prompt_contains_section_instructions(sample_inputs, sample_results):
    system, user = build_memo_prompt(sample_inputs, sample_results)
    assert "Property Overview" in user
    assert "Return Profile" in user
    assert "Key Risks" in user
    assert "Recommendation" in user


def test_build_memo_prompt_returns_two_strings(sample_inputs, sample_results):
    result = build_memo_prompt(sample_inputs, sample_results)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert isinstance(result[1], str)

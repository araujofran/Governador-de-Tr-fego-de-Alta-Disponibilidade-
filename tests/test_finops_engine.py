import pytest
from finops_engine import FinOpsEngine

def test_finops_calculation():
    engine = FinOpsEngine(fx_rate=5.1262)
    
    # Test Gemini 3.6 Flash (Input: $0.75 / 1M, Output: $3.75 / 1M)
    res = engine.calculate_cost(
        provider="google",
        model="gemini-3.6-flash",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        is_free_tier=True
    )

    assert res.actual_cost_brl == 0.0
    assert res.equivalent_cost_usd == 4.5  # $0.75 + $3.75
    assert res.equivalent_cost_brl == round(4.5 * 5.1262, 4)
    assert res.savings_brl == res.equivalent_cost_brl
    assert res.price_status == "CALCULATED"

def test_capacity_projections():
    engine = FinOpsEngine(fx_rate=5.1262)
    projections = engine.calculate_capacity_projections(
        avg_input_tokens_per_call=2000,
        avg_output_tokens_per_call=400
    )

    assert "1000_calls" in projections
    assert "50000_calls" in projections
    proj_1k = projections["1000_calls"]
    assert proj_1k["projected_input_tokens"] == 2_000_000
    assert proj_1k["projected_output_tokens"] == 400_000
    assert proj_1k["equivalent_cost_usd"] > 0.0

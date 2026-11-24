"""
Phase 1 acceptance test: model vs public CFM56-7B26/3 data (ICAO EDB + EASA TCDS).

Tolerances are in reference_data.TOLERANCE_PCT (agreed with the project owner).
Run with:  pytest -m validation   (about 7 minutes)
"""
import pytest

import reference_data as ref

# Also "slow", so `pytest -m "not slow"` (fast tests, used by the edit hook) excludes it.
pytestmark = [pytest.mark.slow, pytest.mark.validation]


@pytest.fixture(scope="module")
def table():
    import validate_cfm56 as v
    _, rows = v.run_validation(log=lambda *a: None)
    return {q: (model, refv, err, tol) for q, model, refv, err, tol, _ in v.comparison_table(rows)}


def test_rated_thrust_reached(table):
    model, refv, _, _ = table["Take-off thrust (kN)"]
    assert model == pytest.approx(refv, rel=1e-6)


@pytest.mark.parametrize("quantity", [
    "OPR at take-off", "BPR at take-off",
    "Fuel flow Take-off (kg/s)", "Fuel flow Climb-out (kg/s)",
    "Fuel flow Approach (kg/s)", "Fuel flow Idle (kg/s)",
])
def test_within_tolerance(table, quantity):
    model, refv, err, tol = table[quantity]
    assert abs(err) <= tol, f"{quantity}: model {model:.3f} vs ref {refv:.3f} ({err:+.1f} %, tol ±{tol} %)"

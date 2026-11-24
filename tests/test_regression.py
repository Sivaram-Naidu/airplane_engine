"""
Regression test: the cruise point must reproduce the Phase 0 baseline.

Baseline recorded 2026-11-24 on Python 3.12, OpenMDAO 3.45.2, pyCycle @ ee7e161,
NumPy 2.5.5 (see baseline/quick_summary_us.csv). These are NOT real-engine numbers;
they come from the pyCycle example inputs (see docs/assumptions.md). The test exists
so that any change to the model shows up as a visible, deliberate diff.
"""
import pytest

pytestmark = pytest.mark.slow

BASELINE = {  # cruise design point, US units
    "airflow_lbm_s": 344.30314,
    "net_thrust_lbf": 5900.0,
    "OPR": 30.093715,
    "BPR": 5.105,
    "TSFC_lbm_per_lbf_hr": 0.63071998,
    "T4_degR": 2857.0,
    "fuel_flow_lbm_s": 1.03368,
}
REL_TOL = 1e-4  # Newton solver converges to ~1e-8; 1e-4 allows for library/platform noise


@pytest.fixture(scope="module")
def cruise():
    import run_engine
    prob = run_engine.build_problem()
    prob["OD_part.PC"] = 1.0
    prob.run_model()
    return (run_engine.summary_row(prob, "DESIGN", "design"),
            run_engine.summary_row(prob, "OD_part", "od"))


@pytest.mark.parametrize("key", BASELINE)
def test_design_point_matches_baseline(cruise, key):
    design, _ = cruise
    assert design[key] == pytest.approx(BASELINE[key], rel=REL_TOL)


@pytest.mark.parametrize("key", BASELINE)
def test_off_design_at_design_conditions_reproduces_design(cruise, key):
    # Self-consistency: running the sized engine at the exact sizing condition and
    # full power must give back the design point. If this fails, the design and
    # off-design halves of the model disagree.
    design, od = cruise
    assert od[key] == pytest.approx(design[key], rel=1e-6)


def test_fuel_flow_consistent_with_tsfc(cruise):
    # TSFC is fuel flow per unit thrust: Wf [lbm/s] = TSFC [lbm/lbf/h] * Fn [lbf] / 3600
    design, _ = cruise
    assert design["fuel_flow_lbm_s"] == pytest.approx(
        design["TSFC_lbm_per_lbf_hr"] * design["net_thrust_lbf"] / 3600.0, rel=1e-6)


def test_si_columns_present_and_consistent(cruise):
    design, _ = cruise
    assert design["net_thrust_kN"] == pytest.approx(26.2445, rel=1e-4)
    assert design["T4_K"] == pytest.approx(1587.22, rel=1e-4)
    assert design["TSFC_g_per_kN_s"] == pytest.approx(17.865, rel=1e-3)

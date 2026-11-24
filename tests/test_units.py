"""Unit conversions: check against independently known reference values."""
import pytest

import units as u


def test_thrust_lbf_to_kn():
    # 1 lbf = 4.4482216152605 N exactly (NIST SP 811)
    assert u.lbf_to_kn(1000.0) == pytest.approx(4.4482216152605)


def test_mass_flow():
    assert u.lbm_s_to_kg_s(1.0) == pytest.approx(0.45359237)


def test_temperature():
    # Water freezing point: 491.67 degR = 273.15 K = 0 degC
    assert u.degr_to_k(491.67) == pytest.approx(273.15)
    assert u.degr_to_c(491.67) == pytest.approx(0.0, abs=1e-9)


def test_altitude():
    assert u.ft_to_m(35000.0) == pytest.approx(10668.0)


def test_tsfc_factor_matches_claude_md_rule_of_thumb():
    # CLAUDE.md quotes x28.33; the exact factor is 28.3254...
    assert u.TSFC_US_TO_SI == pytest.approx(28.3254, abs=1e-4)
    assert u.tsfc_us_to_si(0.6) == pytest.approx(16.995, abs=1e-3)


def test_power_and_pressure():
    assert u.hp_to_kw(1.0) == pytest.approx(0.7457, abs=1e-4)
    assert u.psi_to_kpa(14.696) == pytest.approx(101.325, abs=1e-3)  # 1 standard atmosphere

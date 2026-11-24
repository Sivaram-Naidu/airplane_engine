"""
Run a CFM56-class turbofan: size it at cruise (design point), then check how
it performs at other flight conditions (off-design).

Usage:
    python run_engine.py            # design point + flight sweep
    python run_engine.py --quick    # design point + cruise only (fast check)

Outputs:
    results/summary.csv     one row per operating point
    results/full_report.txt detailed station-by-station report
"""
import csv
import os
import sys
import time

import openmdao.api as om
import pycycle.api as pyc

import units as u
from turbofan_model import HBTF, viewer

# ---------------------------------------------------------------------------
# 1. DESIGN CHOICES  (edit these and re-run to explore)
#    Units: thrust lbf, temperature degR, speeds rpm, altitude ft
# ---------------------------------------------------------------------------
#    Phase 1 (2026-11-24): BPR, hpc_PR and all five efficiencies were tuned by hand so that
#    the model matches public CFM56-7B26/3 sea-level data (ICAO EDB UID 8CM065) within the
#    agreed tolerances; see validate_cfm56.py and docs/assumptions.md. All values remain
#    ASSUMPTIONS: they reproduce public totals, they are not the real engine's internals.
#    Untuned values (pyCycle example) are given in the comments.
# ---------------------------------------------------------------------------
DESIGN = {
    "alt_ft": 35000.0,       # design point = typical cruise altitude (pyCycle example; ASSUMPTION)
    "mach": 0.8,             # typical cruise Mach number (pyCycle example; ASSUMPTION)
    "Fn_lbf": 5900.0,        # net thrust needed at cruise, per engine (pyCycle example; ASSUMPTION)
    "T4_degR": 2857.0,       # cruise turbine inlet temperature, 1587 K (pyCycle example; ASSUMPTION)
    # ASSUMPTION (tuned): cruise BPR 4.73 gives SLS take-off BPR 5.09 vs ICAO 5.1. Example: 5.105.
    "BPR": 4.73,
    "fan_PR": 1.685, "lpc_PR": 1.935,     # pyCycle example; ASSUMPTION
    # ASSUMPTION (tuned): gives SLS take-off OPR 27.9 vs ICAO 27.7. Example: 9.369.
    "hpc_PR": 9.96,
    # ASSUMPTION (tuned): every efficiency = example - 0.015, a single "technology level" knob
    # that brings take-off/climb-out fuel flow within 5 % of ICAO. Example values:
    # fan 0.8948, lpc 0.9243, hpc 0.8707, hpt 0.8888, lpt 0.8996.
    "fan_eff": 0.8798, "lpc_eff": 0.9093, "hpc_eff": 0.8557, "hpt_eff": 0.8738, "lpt_eff": 0.8846,
    "LP_rpm": 4666.1, "HP_rpm": 14705.7,  # pyCycle example; ASSUMPTION (only scale the maps)
}

# Off-design flight conditions (Mach, altitude ft). Ordered from cruise down to
# the runway on purpose: each point starts from the previous solution, which
# helps the Newton solver converge.
FLIGHT_SWEEP = [(0.8, 35000), (0.6, 20000), (0.4, 10000), (0.2, 1000), (0.001, 0)]
POWER_SETTINGS = [1.0, 0.8]   # fraction of max thrust at each condition


# Installed loads: customer (cabin) bleed and shaft power taken by the aircraft.
# They are per-point inputs (not shared cycle parameters) so that test-stand points
# can switch them off: ICAO databank and TCDS ratings assume no customer bleed or
# power offtake (EASA ICAO EDB introduction §3c; EASA TCDS E.004 issue 07, note 2).
# Values from the pyCycle example (ASSUMPTION, see docs/assumptions.md).
INSTALLED_LOADS = {"cust_bleed_frac": 0.0445, "HPX_hp": 250.0}

DEFAULT_OD_POINTS = (("OD_max", "T4"), ("OD_part", "percent_thrust"))


def set_installed_loads(prob, pt, installed=True):
    """Installed = aircraft loads on (flight); installed=False = test stand (ICAO/TCDS)."""
    prob.set_val(f"{pt}.hpc.cust:frac_W", INSTALLED_LOADS["cust_bleed_frac"] if installed else 0.0)
    prob.set_val(f"{pt}.hp_shaft.HPX", INSTALLED_LOADS["HPX_hp"] if installed else 0.0, units="hp")


class CFM56ClassEngine(pyc.MPCycle):
    """Design point + configurable off-design points.

    Default: OD_max (throttle = T4 limit) and OD_part (throttle = % of OD_max thrust).
    A point in "percent_thrust" mode without OD_max has Fn_max as a free input, so it
    acts as a thrust-target point: Fn = PC * Fn_max.
    """

    def initialize(self):
        self.options.declare("od_points", default=DEFAULT_OD_POINTS)
        super().initialize()

    def setup(self):
        d = DESIGN
        self.pyc_add_pnt("DESIGN", HBTF(thermo_method="CEA"))

        # Flow Mach numbers at each station (sets flow areas at design)
        for name, mn in {"inlet": 0.751, "fan": 0.4578, "splitter.MN1": 0.3104,
                         "splitter.MN2": 0.4518, "duct4": 0.3121, "lpc": 0.3059,
                         "duct6": 0.3563, "hpc": 0.2442, "bld3": 0.3, "burner": 0.1025,
                         "hpt": 0.365, "duct11": 0.3063, "lpt": 0.4127, "duct13": 0.4463,
                         "byp_bld": 0.4489, "duct15": 0.4589}.items():
            path = f"DESIGN.{name}" if "." in name else f"DESIGN.{name}.MN"
            self.set_input_defaults(path, mn)
        self.set_input_defaults("DESIGN.splitter.BPR", d["BPR"])
        self.set_input_defaults("DESIGN.LP_Nmech", d["LP_rpm"], units="rpm")
        self.set_input_defaults("DESIGN.HP_Nmech", d["HP_rpm"], units="rpm")

        # Losses, cooling bleeds, power extraction (shared by all points)
        params = {
            "inlet.ram_recovery": 0.999, "duct4.dPqP": 0.0048, "duct6.dPqP": 0.0101,
            "burner.dPqP": 0.054, "duct11.dPqP": 0.0051, "duct13.dPqP": 0.0107,
            "duct15.dPqP": 0.0149, "core_nozz.Cv": 0.9933, "byp_bld.bypBld:frac_W": 0.005,
            "byp_nozz.Cv": 0.9939,
            "hpc.cool1:frac_W": 0.050708, "hpc.cool1:frac_P": 0.5, "hpc.cool1:frac_work": 0.5,
            "hpc.cool2:frac_W": 0.020274, "hpc.cool2:frac_P": 0.55, "hpc.cool2:frac_work": 0.5,
            "bld3.cool3:frac_W": 0.067214, "bld3.cool4:frac_W": 0.101256,
            "hpc.cust:frac_P": 0.5, "hpc.cust:frac_work": 0.5,
            "hpt.cool3:frac_P": 1.0, "hpt.cool4:frac_P": 0.0,
            "lpt.cool1:frac_P": 1.0, "lpt.cool2:frac_P": 0.0,
        }
        for k, v in params.items():
            self.pyc_add_cycle_param(k, v)
        # hpc.cust:frac_W and hp_shaft.HPX are per point: see INSTALLED_LOADS.

        od_points = self.options["od_points"]
        for pt, mode in od_points:
            self.pyc_add_pnt(pt, HBTF(design=False, thermo_method="CEA", throttle_mode=mode))
            self.set_input_defaults(f"{pt}.fc.MN", 0.8)
            self.set_input_defaults(f"{pt}.fc.alt", 35000.0, units="ft")
            self.set_input_defaults(f"{pt}.fc.dTs", 0.0, units="degR")
        names = [p for p, _ in od_points]
        if "OD_max" in names and "OD_part" in names:
            self.connect("OD_max.perf.Fn", "OD_part.Fn_max")

        self.pyc_use_default_des_od_conns()
        self.pyc_connect_des_od("core_nozz.Throat:stat:area", "balance.rhs:W")
        self.pyc_connect_des_od("byp_nozz.Throat:stat:area", "balance.rhs:BPR")
        super().setup()


def build_problem(od_points=DEFAULT_OD_POINTS):
    d = DESIGN
    prob = om.Problem(model=CFM56ClassEngine(od_points=od_points), reports=False)
    prob.setup()
    od_names = [p for p, _ in od_points]
    for pt in ["DESIGN"] + od_names:
        set_installed_loads(prob, pt, installed=True)

    for comp in ("fan", "lpc", "hpc"):
        prob.set_val(f"DESIGN.{comp}.PR", d[f"{comp}_PR"])
        prob.set_val(f"DESIGN.{comp}.eff", d[f"{comp}_eff"])
    prob.set_val("DESIGN.hpt.eff", d["hpt_eff"])
    prob.set_val("DESIGN.lpt.eff", d["lpt_eff"])
    prob.set_val("DESIGN.fc.alt", d["alt_ft"], units="ft")
    prob.set_val("DESIGN.fc.MN", d["mach"])
    prob.set_val("DESIGN.T4_MAX", d["T4_degR"], units="degR")
    prob.set_val("DESIGN.Fn_DES", d["Fn_lbf"], units="lbf")
    for pt, mode in od_points:
        if mode == "T4":
            prob.set_val(f"{pt}.T4_MAX", d["T4_degR"], units="degR")
        else:
            prob.set_val(f"{pt}.PC", 0.8)

    # Initial guesses for the solver (rough values are fine)
    prob["DESIGN.balance.FAR"] = 0.025
    prob["DESIGN.balance.W"] = 100.0
    prob["DESIGN.balance.lpt_PR"] = 4.0
    prob["DESIGN.balance.hpt_PR"] = 3.0
    prob["DESIGN.fc.balance.Pt"] = 5.2
    prob["DESIGN.fc.balance.Tt"] = 440.0
    for pt in od_names:
        prob[f"{pt}.balance.FAR"] = 0.02467
        prob[f"{pt}.balance.W"] = 300
        prob[f"{pt}.balance.BPR"] = d["BPR"]
        prob[f"{pt}.balance.lp_Nmech"] = 5000
        prob[f"{pt}.balance.hp_Nmech"] = 15000
        prob[f"{pt}.hpt.PR"] = 3.0
        prob[f"{pt}.lpt.PR"] = 4.0
        for c in ("fan", "lpc", "hpc"):
            prob[f"{pt}.{c}.map.RlineMap"] = 2.0
    prob.set_solver_print(level=-1)
    return prob


class NotConvergedError(RuntimeError):
    pass


def check_converged(prob, points, tol=1e-6):
    """Raise if any point's residuals are not ~zero after run_model.

    The point solvers use err_on_non_converge=False, so without this check a failed
    solve would print results as if it had succeeded. tol=1e-6 is 100x the Newton
    atol (1e-8); converged points in Phase 0 reached <= 8.4e-9.
    """
    for pt in points:
        norm = prob.model._get_subsystem(pt)._residuals.get_norm()
        if not norm < tol:  # also catches NaN
            raise NotConvergedError(f"Point {pt} did not converge: residual norm {norm:.2e} > {tol:.0e}")


def summary_row(prob, pt, label):
    """One operating point as a flat dict: US columns (model units) then SI columns."""
    g = lambda name: float(prob.get_val(f"{pt}.{name}")[0])
    row = {
        "point": label,
        "mach": g("fc.Fl_O:stat:MN"),
        "alt_ft": g("fc.alt"),
        "airflow_lbm_s": g("inlet.Fl_O:stat:W"),
        "net_thrust_lbf": g("perf.Fn"),
        "OPR": g("perf.OPR"),
        "BPR": g("splitter.BPR"),
        "TSFC_lbm_per_lbf_hr": g("perf.TSFC"),
        "T4_degR": g("burner.Fl_O:tot:T"),
        "fuel_flow_lbm_s": g("burner.Wfuel"),
    }
    row.update({
        "alt_m": u.ft_to_m(row["alt_ft"]),
        "airflow_kg_s": u.lbm_s_to_kg_s(row["airflow_lbm_s"]),
        "net_thrust_kN": u.lbf_to_kn(row["net_thrust_lbf"]),
        "TSFC_g_per_kN_s": u.tsfc_us_to_si(row["TSFC_lbm_per_lbf_hr"]),
        "T4_K": u.degr_to_k(row["T4_degR"]),
        "fuel_flow_kg_s": u.lbm_s_to_kg_s(row["fuel_flow_lbm_s"]),
    })
    return row


def print_tables(rows):
    """Console summary: SI table first, then the same points in US units."""
    print(f"\nSI units\n{'Operating point':34s} {'Thrust kN':>9s} {'Air kg/s':>8s} {'OPR':>6s} {'BPR':>5s} "
          f"{'TSFC g/kN/s':>11s} {'T4 K':>6s} {'Fuel kg/s':>9s}")
    for r in rows:
        print(f"{r['point']:34s} {r['net_thrust_kN']:9.2f} {r['airflow_kg_s']:8.1f} {r['OPR']:6.1f} "
              f"{r['BPR']:5.2f} {r['TSFC_g_per_kN_s']:11.2f} {r['T4_K']:6.0f} {r['fuel_flow_kg_s']:9.4f}")

    print(f"\nUS units (pyCycle native)\n{'Operating point':34s} {'Thrust lbf':>10s} {'OPR':>6s} {'BPR':>5s} "
          f"{'TSFC':>7s} {'T4 degR':>8s}")
    for r in rows:
        print(f"{r['point']:34s} {r['net_thrust_lbf']:10.0f} {r['OPR']:6.1f} {r['BPR']:5.2f} "
              f"{r['TSFC_lbm_per_lbf_hr']:7.4f} {r['T4_degR']:8.0f}")


def main():
    quick = "--quick" in sys.argv
    os.makedirs("results", exist_ok=True)
    prob = build_problem()
    sweep = FLIGHT_SWEEP[:1] if quick else FLIGHT_SWEEP
    settings = POWER_SETTINGS[:1] if quick else POWER_SETTINGS

    rows, start = [], time.time()
    with open("results/full_report.txt", "w") as report:
        for i, (mach, alt) in enumerate(sweep):
            for pt in ("OD_max", "OD_part"):
                prob[f"{pt}.fc.MN"] = mach
                prob[f"{pt}.fc.alt"] = alt
            for pc in settings:
                prob["OD_part.PC"] = pc
                prob.run_model()
                check_converged(prob, ("DESIGN", "OD_max", "OD_part"))
                if i == 0 and pc == settings[0]:
                    rows.append(summary_row(prob, "DESIGN", "DESIGN (cruise sizing)"))
                    viewer(prob, "DESIGN", file=report)
                rows.append(summary_row(prob, "OD_part", f"M{mach} / {alt:.0f} ft / {pc:.0%} power"))
                viewer(prob, "OD_part", file=report)
                print(f"  solved: Mach {mach}, {alt:.0f} ft, {pc:.0%} power")

    with open("results/summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    print_tables(rows)
    print(f"\nDone in {time.time() - start:.0f} s. See results/summary.csv and results/full_report.txt")


if __name__ == "__main__":
    main()

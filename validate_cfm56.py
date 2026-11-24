"""
Phase 1: compare the model with public CFM56-7B26/3 data at sea-level static (ISA).

The engine is still sized at cruise (DESIGN). One off-design point "OD" runs in
thrust-target mode (Fn = PC * Fn_max) with aircraft loads switched OFF, matching the
ICAO/TCDS test-stand conditions (see reference_data.py). The solver needs a gradual
path, so we walk cruise -> sea level, ramp thrust up to the rated value, then step
down through the ICAO power settings.

Usage:
    python validate_cfm56.py                        # current DESIGN values
    python validate_cfm56.py --set BPR=5.3 --set hpc_PR=9.0 --tag try1   # tuning trial (no code edit)

Outputs: results/validation_cfm56_7b26.csv and .md
"""
import csv
import os
import sys
import time

import reference_data as ref
import run_engine as re_
import units as u

KN_TO_LBF = 1000.0 / u.LBF_TO_N
RATED_LBF = ref.RATED_THRUST_KN * KN_TO_LBF

# Cruise -> sea level. Thrust targets are 90 % of the max-thrust values from the Phase 0
# baseline (baseline/full_summary_us.csv) so every step is reachable.
WALK = [(0.8, 35000, 0.9 * 5900), (0.6, 20000, 0.9 * 8884), (0.4, 10000, 0.9 * 12101),
        (0.2, 1000, 0.9 * 16555), (0.001, 0, 0.9 * 20993)]
# At sea-level static: ramp the thrust target up to the rated value...
RAMP_LBF = [21000.0, 23500.0, RATED_LBF]
# ...then step down through the ICAO power settings (extra steps help convergence).
PC_STEPS = [1.0, 0.85, 0.6, 0.3, 0.15, 0.07]


def _row(prob, label):
    g = lambda name: float(prob.get_val(f"OD.{name}")[0])
    return {
        "point": label,
        "thrust_kN": u.lbf_to_kn(g("perf.Fn")),
        "OPR": g("perf.OPR"),
        "BPR": g("splitter.BPR"),
        "fuel_kg_s": u.lbm_s_to_kg_s(g("burner.Wfuel")),
        "T4_K": u.degr_to_k(g("burner.Fl_O:tot:T")),
        "airflow_kg_s": u.lbm_s_to_kg_s(g("inlet.Fl_O:stat:W")),
        "N1_rpm": float(prob.get_val("OD.LP_Nmech", units="rpm")[0]),
        "N2_rpm": float(prob.get_val("OD.HP_Nmech", units="rpm")[0]),
    }


def _solve(prob):
    prob.run_model()
    re_.check_converged(prob, ("DESIGN", "OD"))


def run_validation(overrides=None, log=print):
    """Run the validation path. overrides: dict of DESIGN keys -> values (for tuning)."""
    if overrides:
        unknown = set(overrides) - set(re_.DESIGN)
        if unknown:
            raise KeyError(f"Unknown DESIGN keys: {sorted(unknown)}")
        re_.DESIGN.update(overrides)

    prob = re_.build_problem(od_points=(("OD", "percent_thrust"),))
    re_.set_installed_loads(prob, "OD", installed=False)  # test stand: no bleed, no HPX
    prob["OD.PC"] = 1.0

    for mach, alt, fn in WALK:
        prob["OD.fc.MN"], prob["OD.fc.alt"], prob["OD.Fn_max"] = mach, alt, fn
        _solve(prob)
        log(f"  walk: M{mach} {alt} ft, Fn {u.lbf_to_kn(fn):.1f} kN")
    design = re_.summary_row(prob, "DESIGN", "DESIGN (cruise sizing)")

    for fn in RAMP_LBF:
        prob["OD.Fn_max"] = fn
        _solve(prob)
        log(f"  ramp: Fn {u.lbf_to_kn(fn):.1f} kN, T4 {u.degr_to_k(float(prob['OD.burner.Fl_O:tot:T'][0])):.0f} K")

    targets = {frac: (name, ff) for name, frac, ff in ref.LTO_POINTS}
    rows = []
    for pc in PC_STEPS:
        prob["OD.PC"] = pc
        _solve(prob)
        if pc in targets:
            name, ff_ref = targets[pc]
            r = _row(prob, name)
            r["fuel_ref_kg_s"] = ff_ref
            r["fuel_err_pct"] = 100.0 * (r["fuel_kg_s"] - ff_ref) / ff_ref
            rows.append(r)
            log(f"  {name}: fuel {r['fuel_kg_s']:.3f} kg/s (ICAO {ff_ref:.3f}, {r['fuel_err_pct']:+.1f} %)")
    return design, rows


def comparison_table(rows):
    """List of (quantity, model, ICAO, error %, tolerance %, pass)."""
    to = rows[0]
    out = []

    def add(q, model, refv, tol_key):
        err = 100.0 * (model - refv) / refv
        tol = ref.TOLERANCE_PCT.get(tol_key)
        out.append((q, model, refv, err, tol, tol is None or abs(err) <= tol))

    out.append(("Take-off thrust (kN)", to["thrust_kN"], ref.RATED_THRUST_KN,
                100.0 * (to["thrust_kN"] - ref.RATED_THRUST_KN) / ref.RATED_THRUST_KN, None, True))
    add("OPR at take-off", to["OPR"], ref.OPR_TAKEOFF, "OPR")
    add("BPR at take-off", to["BPR"], ref.BPR_TAKEOFF, "BPR")
    for r in rows:
        add(f"Fuel flow {r['point']} (kg/s)", r["fuel_kg_s"], r["fuel_ref_kg_s"], r["point"])
    return out


def write_outputs(design, rows, table, overrides, elapsed, tag=""):
    os.makedirs("results", exist_ok=True)
    base = "results/validation_cfm56_7b26" + (f"_{tag}" if tag else "")
    with open(base + ".csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    to = rows[0]
    lines = [
        f"# Validation: model vs {ref.ENGINE} (ICAO EDB UID {ref.EDB_UID}, EASA TCDS E.004)",
        "",
        f"Sea-level static, ISA, no customer bleed or power offtake. Overrides: {overrides or 'none'}. "
        f"Run time {elapsed:.0f} s.",
        "",
        "| Quantity | Model | ICAO / TCDS | Error % | Tolerance % | Pass |",
        "|---|---|---|---|---|---|",
    ]
    for q, m, r, e, tol, ok in table:
        tol_s = "set by construction" if tol is None else f"±{tol:.0f}"
        lines.append(f"| {q} | {m:.3f} | {r:.3f} | {e:+.1f} | {tol_s} | {'yes' if ok else '**NO**'} |")
    lines += [
        "",
        "Model-only values at take-off (no public reference used for tuning):",
        "",
        f"- T4 needed for rated thrust: {to['T4_K']:.0f} K (cruise design T4: {u.degr_to_k(re_.DESIGN['T4_degR']):.0f} K)",
        f"- Airflow: {to['airflow_kg_s']:.1f} kg/s",
        f"- N1 {to['N1_rpm']:.0f} rpm (TCDS limit {ref.N1_MAX_RPM}), N2 {to['N2_rpm']:.0f} rpm (TCDS limit {ref.N2_MAX_RPM})."
        " Model rpm are scaled from the pyCycle example's design speeds, so they are indicative only.",
        "",
        f"Cruise design point: thrust {design['net_thrust_kN']:.2f} kN, OPR {design['OPR']:.1f}, "
        f"BPR {design['BPR']:.2f}, TSFC {design['TSFC_g_per_kN_s']:.2f} g/(kN·s).",
    ]
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return "\n".join(lines)


def parse_args(argv):
    """--set KEY=VALUE (repeatable) and --tag NAME (suffix for output files)."""
    out, tag = {}, ""
    for i, a in enumerate(argv):
        if a == "--set":
            k, v = argv[i + 1].split("=")
            out[k] = float(v)
        elif a == "--tag":
            tag = argv[i + 1]
    return out, tag


def main():
    overrides, tag = parse_args(sys.argv[1:])
    start = time.time()
    design, rows = run_validation(overrides)
    table = comparison_table(rows)
    print("\n" + write_outputs(design, rows, table, overrides, time.time() - start, tag))


if __name__ == "__main__":
    main()

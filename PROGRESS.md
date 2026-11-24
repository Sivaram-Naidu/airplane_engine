# Progress log

## Phase 0: Orientation (done 2026-11-24)

### Built
- **Environment:** `.venv` with Python 3.12, OpenMDAO 3.45.2, pyCycle @ `ee7e161`, NumPy 2.5.5.
- **git** repository + `.gitignore`.
- **`units.py`:** exact US → SI conversions (NIST SP 811). The console and `results/summary.csv`
  now show SI (kN, kg/s, K, g/(kN·s), m) next to US units.
- **Tests (22, all passing):** 6 unit-conversion tests (< 1 s) plus 16 slow tests (~2 min):
  cruise regression against the baseline, a design/off-design self-consistency check, a
  fuel-flow = TSFC × thrust check, and SI columns.
- **Baseline:** `baseline/quick_summary_us.csv`, `baseline/full_summary_us.csv`.
- **Docs:** `docs/architecture.md` (code walkthrough + review findings), `docs/glossary.md`
  (20 terms), `docs/assumptions.md` (data provenance), `docs/tools.md` (licences).

### Baseline results (pyCycle example inputs, NOT CFM56-7B data)
| Operating point | Thrust kN | OPR | BPR | TSFC g/(kN·s) | T4 K |
|---|---|---|---|---|---|
| Cruise design, M0.80 / 35,000 ft | 26.24 | 30.1 | 5.11 | 17.87 | 1587 |
| M0.6 / 20,000 ft, max | 39.52 | 25.6 | 5.54 | 16.28 | 1587 |
| M0.4 / 10,000 ft, max | 53.83 | 23.5 | 5.74 | 14.24 | 1587 |
| M0.2 / 1,000 ft, max | 73.64 | 21.1 | 5.87 | 11.99 | 1587 |
| Sea-level static, max | 93.38 | 21.0 | 5.82 | 9.51 | 1587 |

### Known issues found
1. ~~Full sweep takes ~3 h~~ **Resolved: not a model problem.** The Windows power log shows the
   laptop was in Modern Standby (sleep) from 10:34 to 13:31 during that run. A per-point solver
   diagnostic re-run took **474 s (~8 min)** for all 10 conditions. Every point converged in 4–9
   Newton iterations with residual ≤ 8.4e-9 (tolerance 1e-8), so the baseline numbers are
   genuinely converged. Remaining cost: ~4 s per Newton iteration (CEA chemistry). That is a speed-up
   candidate for Phase 2, and acceptable for now.
   Risk noted: the solvers use `err_on_non_converge=False`, so a non-converged point would still
   print "solved". A convergence guard is proposed for Phase 1.
2. "Max" power uses the cruise T4 everywhere, so sea-level thrust is too low for a takeoff rating (Phase 1).
3. `thermo_method` argument is silently overridden in `HBTF.setup()` (cosmetic, Phase 2).

## Phase 1: Validate against CFM56-7B26 (next)

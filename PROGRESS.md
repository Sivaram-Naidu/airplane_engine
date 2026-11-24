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

## Phase 1: Validate against CFM56-7B26/3 (done 2026-11-24)

### Built
- **Project config:** `.claude/settings.json` (permissions; a fast-test hook after `.py` edits),
  CLAUDE.md "IP and provenance" rules, `docs/originality_log.md`.
- **Public reference data:** `reference_data.py`, where every number cites ICAO EDB v32B UID 8CM065,
  the EDB introduction, EASA TCDS E.004 issue 07, or the ICAO LTO settings (via UK CAA). Raw files are
  downloaded with `data/fetch_reference_data.py` and not committed (© EASA; see data/README.md).
- **Model changes (`run_engine.py`):**
  - configurable off-design points;
  - customer bleed and power offtake are now per point, so test-stand points switch them off;
  - **convergence guard** (`check_converged`): a non-converged point now raises instead of
    printing "solved".
- **Takeoff rating:** `validate_cfm56.py` solves for the T4 that gives the rated 117 kN at
  sea-level static, then runs the 4 ICAO power settings (100/85/30/7 %). `--set KEY=VALUE --tag NAME`
  runs tuning trials without editing code.
- **Tuning (by hand, 4 trials):** cruise design BPR 5.105 → 4.73; HPC PR 9.369 → 9.96; all
  efficiencies − 0.015. Details and all trials are in docs/assumptions.md.
- **Tests:** `tests/test_validation.py` (marker `validation`, about 7 min) enforces the agreed
  tolerances. The regression baseline was re-recorded deliberately (`baseline/phase1_*`).

### Results: model vs CFM56-7B26/3 (sea-level static, ISA, no bleed/offtake)
| Quantity | Model | ICAO / TCDS | Error | Tolerance |
|---|---|---|---|---|
| Takeoff thrust | 117.0 kN | 117.0 kN | 0 (set) | n/a |
| OPR at takeoff | 27.89 | 27.7 | +0.7 % | ±3 % |
| BPR at takeoff | 5.09 | 5.1 | −0.2 % | ±5 % |
| Fuel flow, takeoff | 1.171 kg/s | 1.213 | −3.4 % | ±5 % |
| Fuel flow, climb-out (85 %) | 0.963 | 0.986 | −2.3 % | ±5 % |
| Fuel flow, approach (30 %) | 0.328 | 0.331 | −0.9 % | ±10 % |
| Fuel flow, idle (7 %) | 0.128 | 0.108 | +18.7 % | ±20 % |

Model outputs with no public reference: takeoff T4 ≈ 1656 K (cruise 1587 K); cruise TSFC 18.55 g/(kN·s),
up from 17.87 untuned because the less efficient components cost fuel everywhere.

### Known limitations
1. **Idle is near its limit (+18.7 %).** The uniform efficiency penalty hurts low power about twice as much
   as high power. Fixing this needs engine-specific component maps, which are not public.
2. **Cruise is not validated.** ICAO data are sea level only, and the EDB introduction §3c says they
   must not be used for cruise efficiency.
3. **Non-unique tuning:** 7 knobs, 6 targets. The tuned values reproduce totals; they are not the
   real engine's internals.
4. **`run_engine.py` "max power" still uses the cruise T4 everywhere.** The takeoff rating lives
   in `validate_cfm56.py` (T4 solved for rated thrust).
5. **Model rpm are indicative only:** design speeds come from the pyCycle example, not the TCDS.

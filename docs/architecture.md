# Architecture walkthrough

A code-review style tour of the model, written for software developers. Engine
terms are defined in [glossary.md](glossary.md).

## 1. The big picture

The model answers one question: **given these design choices and this flight
condition, what thrust and fuel flow do I get?**

It is not a time-stepping simulation. Each "operating point" is a **steady state**:
a set of nonlinear equations that a Newton solver drives to zero, like a
spreadsheet with circular references that Excel iterates until it settles.

```
run_engine.py                         turbofan_model.py
-------------                         -----------------
DESIGN dict  ──► CFM56ClassEngine     HBTF (one operating point)
                 (pyc.MPCycle)          components + connections + balances
                   ├─ DESIGN  = HBTF(design=True)        sizes the hardware
                   ├─ OD_max  = HBTF(design=False, T4)   max power at a flight condition
                   └─ OD_part = HBTF(design=False, %Fn)  part power at the same condition
                 build_problem() → set inputs + initial guesses
                 main() → sweep flight conditions → CSV, report, console tables
```

## 2. `turbofan_model.py`: one operating point (`HBTF`)

### 2a. Components (the nodes)

`setup()` adds about 20 subsystems. The airflow passes through them in this order
(numbers are the standard station numbers used in reports):

```
fc ─► inlet ─► fan ─► splitter ─┬─► duct4 ─► lpc ─► duct6 ─► hpc ─► bld3 ─► burner ─► hpt ─► duct11 ─► lpt ─► duct13 ─► core_nozz
 0       2      21              │   (core stream)            3              4                         5                  (8)
                                └─► byp_bld ─► duct15 ─► byp_nozz
                                    (bypass stream, ~5x the core flow)          (18)

lp_shaft: fan + lpc  ◄── powered by ── lpt      (3 ports, no gearbox)
hp_shaft: hpc        ◄── powered by ── hpt      (2 ports)
perf:     adds up nozzle thrust, ram drag, fuel → Fn, TSFC, OPR
```

Each component is a function from inlet flow state (pressure, temperature, mass
flow, composition) to outlet flow state. `pyc_connect_flow(a, b)` wires a whole
bundle of variables at once, like passing a struct instead of 10 arguments.

**Bleeds** are side channels: `hpc.cool1/cool2` and `bld3.cool3/cool4` take air
from the compressor and feed it back into the turbines as cooling air. `hpc.cust`
is "customer" bleed taken by the aircraft (cabin air). `byp_bld` is a small
leak from the bypass stream.

**Shafts** are the shared budget: each spool's turbine produces power and its
compressors spend it. The shaft component reports net power, and the solver must
drive it to zero (steady state means no acceleration). `hp_shaft.HPX` is a
250 hp power draw for the aircraft's generators and pumps.

### 2b. Balances (the constraints)

`om.BalanceComp` turns "I want X to equal Y" into an unknown the solver adjusts.
The unknowns and constraints differ between the two modes. **This is the key
idea of the whole model.**

| | **Design mode** (sizing) | **Off-design mode** (hardware frozen) |
|---|---|---|
| Fixed by you | pressure ratios, efficiencies, BPR, station Mach numbers, T4, thrust | flight condition, throttle (T4 or % thrust) |
| Solver adjusts | air mass flow `W`, fuel-air ratio `FAR`, turbine pressure ratios | `W`, `FAR`, `BPR`, both shaft speeds (plus map positions inside components) |
| Constraints | Fn = Fn_DES; T4 = T4_MAX; both shafts net power = 0 | nozzle areas = the design areas; T4 = target (or Fn = PC × Fn_max); both shafts net power = 0 |
| Output | **flow areas and map scaling** (the "hardware") | performance of that fixed hardware |

Analogy: the design point is like choosing the server size from a target load.
Off-design runs the same server under a different load. You can no longer pick
the size; you find out what throughput and latency it delivers.

### 2c. Solver

A Newton solver with an Armijo line search and a direct (LU) linear solver,
`atol=1e-8`. `solve_subsystems=True` lets inner components converge themselves
first. Newton needs a good starting guess, which explains the guesses in
`build_problem()` and the cruise-to-ground order of the sweep.

### 2d. `viewer()`

Prints the station-by-station report (`results/full_report.txt`) using pyCycle's
built-in printers. It is the debugger's "watch window" for every flow station.

## 3. `run_engine.py`: the driver

1. **`DESIGN` dict**: all user-tunable design choices. In Phase 0 these are the
   pyCycle example's values, not CFM56 data (see [assumptions.md](assumptions.md)).
2. **`CFM56ClassEngine(pyc.MPCycle)`**: a multi-point model that puts the DESIGN,
   OD_max and OD_part points in one problem.
   - `set_input_defaults(... .MN ...)` sets the flow Mach number at each station.
     Together with the mass flow, this fixes the **flow area**, so it is a
     sizing choice.
   - `pyc_add_cycle_param` sets losses and bleed fractions shared by all points.
   - `pyc_use_default_des_od_conns()` and `pyc_connect_des_od(...)` copy the
     design's areas and map scaling into the off-design points. This step freezes
     the hardware.
   - `OD_max.perf.Fn → OD_part.Fn_max`: part power is defined as a percentage
     of max thrust *at the same flight condition*.
3. **`build_problem()`**: sets design inputs, then initial guesses.
4. **`main()`**: loops over `FLIGHT_SWEEP` (cruise down to the runway) × `POWER_SETTINGS`.
   Each `run_model()` re-solves all three points. The previous solution is the
   starting guess for the next one (a "warm start").
5. **`summary_row()` / `print_tables()`**: extract results, adding SI columns
   (added in Phase 0, see `units.py`).

## 4. Review findings (Phase 0)

| # | Finding | Severity | Action |
|---|---|---|---|
| 1 | All `DESIGN` numbers come from the generic pyCycle example, not CFM56-7B data. | High (for our goal) | Documented in assumptions.md. Phase 1 replaces them with sourced values. |
| 2 | "Max power" uses the *cruise* T4 everywhere, so takeoff thrust is underestimated. | High (for validation) | Already noted in README. Phase 1 adds a takeoff rating. |
| 3 | `HBTF.setup()` overrides the `thermo_method` option with a hard-coded `USE_TABULAR = False`, so the argument passed in `run_engine.py` has no effect. | Low (misleading, harmless today) | Left as is. Revisit in the Phase 2 refactor. |
| 4 | Runtime: `--quick` takes about 2 min on this machine (README said ~30 s), and the full 10-point sweep takes ~8 min (a first run took 3 h because the laptop went to sleep). Each Newton iteration costs ~4 s. CEA thermo (full chemical equilibrium) is the main cost; `TABULAR` would be faster but gives slightly different numbers. | Medium (slows iteration) | README updated. Speed-up candidate for Phase 2. |
| 5 | The summary records `OD_part` only. At 100 % power it equals `OD_max`, so nothing is lost. | Info | None |
| 6 | There was no version control and no tests. | Medium | git + pytest added in Phase 0. |
| 7 | Newton solvers have `err_on_non_converge=False` and solver printing is off, so a point that fails to converge still prints "solved". All current points do converge (checked). | Medium (silent wrong answers later) | Add a convergence guard in Phase 1. |

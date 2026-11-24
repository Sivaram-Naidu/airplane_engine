# Project context for Claude Code

## Goal
Learning project: understand and model civil high-bypass turbofan engines
(starting with a CFM56-class engine), as groundwork for indigenous engine design.
Only public, open sources are used.

## Files
- `turbofan_model.py`: physics of one operating point (HBTF class), adapted from the
  official pyCycle example (Apache 2.0, keep the attribution header).
- `run_engine.py`: design inputs (DESIGN dict), flight sweep, CSV and report output.
- `units.py`: US -> SI conversions (display only).
- `tests/`: pytest; `slow` marker = runs the pyCycle model.
- `baseline/`: recorded reference outputs used by regression tests.
- `docs/`: architecture, glossary, assumptions (data provenance), tools (licences).
- `PROGRESS.md`: phase log, update at the end of each phase.
- `results/`: generated output, safe to delete.

## Conventions
- pyCycle works in US units: lbf, lbm/s, degR, ft, rpm. Convert to SI only for display
  (1 lbf = 4.448 N, degC = degR/1.8 - 273.15, TSFC lbm/(lbf*h) x 28.33 = g/(kN*s)).
- Off-design points must be solved in a gradual sequence (cruise -> ground). If a new
  point fails to converge, insert intermediate Mach/altitude steps rather than
  changing solver settings first.
- Use the project venv: `.venv/Scripts/python.exe` (Python 3.12).
- `python run_engine.py --quick` (~2 min) to sanity-check any change before a full run;
  `pytest -m "not slow"` for fast tests, `pytest` for all.
- Never invent engine data: cite a public source or label it ASSUMPTION in code and in
  docs/assumptions.md. Check licences of new tools in docs/tools.md.

## Validation sources
- ICAO Aircraft Engine Emissions Databank (EASA website): takeoff thrust, OPR, BPR,
  fuel flow for certified engines.
- EASA / FAA Type Certificate Data Sheets for ratings and limits.
- NASA NTRS: Energy Efficient Engine (E3) reports, pyCycle and N+3 papers.

## Roadmap
1. Match CFM56-7B public data (ICAO databank) by tuning DESIGN values.
2. Add a separate takeoff rating (higher T4) and compare OPR/fuel flow to ICAO.
3. Plot a flight envelope (thrust and TSFC vs Mach/altitude).
4. Parameter studies: BPR, OPR, T4 vs fuel burn.
5. Geared turbofan (study pyCycle example_cycles/N+3ref and NASA AGTF30).

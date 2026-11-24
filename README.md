# Indian Turbofan Starter: CFM56-class engine model

A working performance model of a CFM56-class airliner engine (the type on
A320s and older 737s), built with NASA's open-source pyCycle. You can change
design choices and see how thrust and fuel burn respond.

## Do I need a GPU?
No. This is engine *cycle* analysis: it runs on any normal laptop CPU.
The quick check takes about 2 minutes and the full sweep about 8 minutes.
Keep the laptop awake during a full run (sleep pauses it). A GPU only becomes useful much later, for
heavy 3D CFD of blades, and even then a multi-core CPU is the main requirement.

## Setup (Windows, macOS or Linux)
1. Install Python 3.12 from python.org (tested; 3.14 not yet tested with pyCycle) (on Windows, tick "Add Python to PATH").
   Also install Git (git-scm.com).
2. Open a terminal in this folder and create a virtual environment:
   ```
   py -3.12 -m venv .venv          # or: python3.12 -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Check it works (about 2 minutes; CEA chemistry is slow):
   ```
   python run_engine.py --quick
   ```
   Expected cruise result: thrust 5900 lbf (26.24 kN), OPR 30.1, BPR 5.11,
   TSFC 0.6307 lbm/(lbf·h) (17.87 g/(kN·s)), T4 2857 °R (1587 K).
   Output is shown in SI and US units.
5. Full run (cruise down to the runway, about 8 minutes):
   ```
   python run_engine.py
   ```
   Results go to `results/summary.csv` and `results/full_report.txt`.

## Validate against the real CFM56-7B26/3 (Phase 1)
```
python data/fetch_reference_data.py   # once: downloads the public ICAO/EASA source files
python validate_cfm56.py              # about 7 minutes; writes results/validation_cfm56_7b26.md
```
Compares takeoff thrust, OPR, BPR and fuel flow at the 4 ICAO power settings with public
data. The current result is in PROGRESS.md (all within the agreed tolerances).

## Tests
```
pytest -m "not slow"   # unit tests, under a second
pytest                 # also runs the cruise regression test (about 2 minutes)
pytest -m validation   # Phase 1 validation against ICAO data (about 7 minutes)
```

## Docs
- `docs/architecture.md`: code walkthrough (how the model and solver fit together)
- `docs/glossary.md`: 20 engine terms explained for developers
- `docs/assumptions.md`: where every number comes from
- `docs/tools.md`: open-source tools and their licences
- `PROGRESS.md`: phase-by-phase log

## Using it with Claude Code
Install Claude Code, open a terminal in this folder and run `claude`. It reads
`CLAUDE.md` automatically, so it knows the project. Good first prompts:
- "Explain what each component in turbofan_model.py does, in simple terms."
- "Convert the summary table output to SI units."
- "Plot thrust and TSFC against altitude from results/summary.csv."
- "Increase BPR to 6 and T4 by 100 degR, run it, and explain what changed."

## What the numbers mean
- **OPR** overall pressure ratio: how much the compressors squeeze the air.
- **BPR** bypass ratio: air going around the core vs through it.
- **TSFC** fuel burned per unit thrust per hour. Lower is better.
- **T4** turbine inlet temperature: the hottest point, limited by blade materials.

Note: this model uses the same T4 limit everywhere. Real engines allow a hotter
takeoff rating, so the sea-level thrust and OPR here are lower than a real
CFM56-7B's takeoff figures. Adding a takeoff rating is roadmap step 2 in CLAUDE.md.

## Credits
Model adapted from the official pyCycle example (NASA Glenn / OpenMDAO, Apache 2.0).

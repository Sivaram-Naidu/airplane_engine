# Assumptions and data provenance

Rule: every number in the model either cites a public source or is labelled
**ASSUMPTION** here (and in a code comment once the value is changed from the
example).

## Status after Phase 0

**None of the current model inputs is CFM56-7B data.** All values in
`run_engine.py` (`DESIGN`, station Mach numbers, losses, bleeds, `HPX`) and the
component maps in `turbofan_model.py` are copied unchanged from the pyCycle example
`example_cycles/high_bypass_turbofan.py` at commit
[`ee7e161`](https://github.com/OpenMDAO/pyCycle/tree/ee7e16126a7a54b5fe35292c53b7eb4e9572620b)
(Apache 2.0). The example does not document where its values came from, so we
treat them as a **generic high-bypass turbofan of roughly CFM56 size**, not as a
description of any real engine.

| Input | Value | Source | Status |
|---|---|---|---|
| Design altitude / Mach | 35,000 ft / 0.80 | pyCycle example | ASSUMPTION: typical cruise; Phase 1 will justify |
| Design net thrust | 5,900 lbf (26.2 kN) | pyCycle example | ASSUMPTION: to be checked against public CFM56-7B cruise data |
| T4 (cruise and "max") | 2,857 °R (1,587 K) | pyCycle example | ASSUMPTION |
| BPR | 5.105 | pyCycle example | ASSUMPTION: compare to ICAO databank BPR in Phase 1 |
| Fan / LPC / HPC pressure ratio | 1.685 / 1.935 / 9.369 | pyCycle example | ASSUMPTION |
| Component efficiencies | fan 0.8948, LPC 0.9243, HPC 0.8707, HPT 0.8888, LPT 0.8996 | pyCycle example | ASSUMPTION |
| Spool speeds | LP 4,666 rpm, HP 14,706 rpm | pyCycle example | ASSUMPTION: TCDS lists rotor speed limits, to be checked in Phase 1 |
| Station Mach numbers | see `run_engine.py` | pyCycle example | ASSUMPTION (they set flow areas) |
| Duct pressure losses, nozzle Cv | see `run_engine.py` | pyCycle example | ASSUMPTION |
| Cooling / customer bleed fractions | see `run_engine.py` | pyCycle example | ASSUMPTION |
| Power extraction HPX | 250 hp | pyCycle example | ASSUMPTION |
| Component maps | `pyc.FanMap`, `LPCMap`, `HPCMap`, `HPTMap`, `LPTMap` | pyCycle built-in generic maps | ASSUMPTION: generic shapes scaled to the design point |
| Atmosphere | standard day (ISA), `dTs = 0` | pyCycle `FlightConditions` | Standard model |
| Fuel / thermo | Jet-A, CEA chemical equilibrium with JANAF data | pyCycle built-in | Standard model |

## Unit conversion factors
Exact by definition (NIST SP 811, Appendix B). See `units.py`.

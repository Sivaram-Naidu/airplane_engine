# Assumptions and data provenance

Rule: every number in the model either cites a public source or is labelled
**ASSUMPTION** here (and in a code comment once the value is changed from the
example).

## Status after Phase 1 (2026-11-24)

Seven inputs were **tuned** so that the model reproduces public CFM56-7B26/3 sea-level data
(ICAO EDB UID 8CM065, EASA TCDS E.004). Tuning means the model's *totals* match. It does **not**
mean these are the real engine's internal values, which are not public. There are more knobs
than targets, so other combinations could match equally well.

| Input | Example value | Tuned value | Why (target it moves) |
|---|---|---|---|
| Cruise design BPR | 5.105 | **4.73** | SLS take-off BPR → 5.09 (ICAO 5.1) |
| HPC pressure ratio | 9.369 | **9.96** | SLS take-off OPR → 27.9 (ICAO 27.7) |
| All 5 component efficiencies | fan 0.8948, LPC 0.9243, HPC 0.8707, HPT 0.8888, LPT 0.8996 | **each − 0.015** | take-off/climb-out fuel flow within 5 % of ICAO |

Tuning trials (all in `results/validation_cfm56_7b26_*.md`, generated locally):

| Trial | Change | OPR err | BPR err | Fuel T/O | C/O | App | Idle |
|---|---|---|---|---|---|---|---|
| untuned | none | −6.0 % | +8.0 % | −8.2 % | −7.6 % | −8.4 % | +5.4 % |
| A | BPR 4.73 | −4.6 % | −0.4 % | −4.9 % | −4.7 % | −6.4 % | +6.7 % |
| B | A + hpc_PR 9.96 | +1.1 % | −0.3 % | −5.9 % | −5.7 % | −7.3 % | +5.8 % |
| **C (adopted)** | B + eff − 0.015 | +0.7 % | −0.2 % | −3.4 % | −2.3 % | −0.9 % | +18.7 % |
| D | B + eff − 0.030 | −0.2 % | −0.1 % | 0.0 % | +1.9 % | +6.7 % | +36.7 % (fails) |

Known limitation: a uniform efficiency penalty raises idle fuel about twice as fast as
take-off fuel, so idle (+18.7 %) is near its ±20 % limit. Generic pyCycle maps are least
reliable at low power. Better low-power fidelity needs engine-specific maps, which are not public.

Other Phase 1 modelling choices:

| Choice | Value | Source / status |
|---|---|---|
| Test-stand points: customer bleed, power offtake | 0, 0 | ICAO EDB columns "Loads Power Extraction" = 0 kW, "Stage Bleed" = 0 %; EDB intro §3c; TCDS note 2 |
| Inlet ram recovery at test stand | 0.999 (unchanged) | TCDS note 2 assumes 100 %; ASSUMPTION, ~0.1 % effect, kept for simplicity |
| Take-off T4 | **output**, about 1656 K | Solved so that Fn = 117 kN. No public value to compare against |
| Path cruise → SLS | thrust targets 90 % of Phase 0 max | numerical only (solver convergence), no physical meaning |

## Status after Phase 0

**None of the model inputs was CFM56-7B data.** All values in
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

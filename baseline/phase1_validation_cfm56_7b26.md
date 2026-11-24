# Validation: model vs CFM56-7B26/3 (ICAO EDB UID 8CM065, EASA TCDS E.004)

Sea-level static, ISA, no customer bleed or power offtake. Overrides: none. Run time 424 s.

| Quantity | Model | ICAO / TCDS | Error % | Tolerance % | Pass |
|---|---|---|---|---|---|
| Take-off thrust (kN) | 117.000 | 117.000 | -0.0 | set by construction | yes |
| OPR at take-off | 27.886 | 27.700 | +0.7 | ±3 | yes |
| BPR at take-off | 5.090 | 5.100 | -0.2 | ±5 | yes |
| Fuel flow Take-off (kg/s) | 1.171 | 1.213 | -3.4 | ±5 | yes |
| Fuel flow Climb-out (kg/s) | 0.963 | 0.986 | -2.3 | ±5 | yes |
| Fuel flow Approach (kg/s) | 0.328 | 0.331 | -0.9 | ±10 | yes |
| Fuel flow Idle (kg/s) | 0.128 | 0.108 | +18.7 | ±20 | yes |

Model-only values at take-off (no public reference used for tuning):

- T4 needed for rated thrust: 1656 K (cruise design T4: 1587 K)
- Airflow: 375.0 kg/s
- N1 4645 rpm (TCDS limit 5382), N2 15417 rpm (TCDS limit 15183). Model rpm are scaled from the pyCycle example's design speeds, so they are indicative only.

Cruise design point: thrust 26.24 kN, OPR 32.0, BPR 4.73, TSFC 18.55 g/(kN·s).

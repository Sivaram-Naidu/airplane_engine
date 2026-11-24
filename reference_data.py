"""
Public reference data for the CFM56-7B26/3 validation (Phase 1).

Every number here is copied from a cited public source. Raw source files are NOT
redistributed in this repo; run `python data/fetch_reference_data.py` to download them.

Sources (accessed 2026-11-24):
  [EDB]  ICAO Aircraft Engine Emissions Databank, issue v32B (11/2026), hosted by EASA:
         https://www.easa.europa.eu/en/domains/environment/icao-aircraft-engine-emissions-databank
         Sheet "Gaseous Emissions and Smoke", row UID 8CM065, "CFM56-7B26/3" (Tech Insertion),
         Data Status C (certification), not superseded. Remark: "Ref. GE REPORT CR-2097/3 Rev1".
  [EDBI] "Introduction to the ICAO Engine Emissions Databank", EASA (edb-introduction_text-rev3.pdf):
         §3c fuel flows are sea-level static, fixed power settings, no customer bleed or power
         offtake, and must not be used for fuel efficiency at other conditions;
         §4 definitions: BPR at max thrust SLS ISA; pressure ratio at take-off rating SLS ISA;
         rated output = max take-off thrust at ISA SLS.
  [TCDS] EASA Type-Certificate Data Sheet E.004, CFM56-7B series, issue 07, 9 January 2023:
         https://www.easa.europa.eu/en/downloads/7795/en
  [LTO]  ICAO Annex 16 Vol II LTO cycle thrust settings (take-off 100 %, climb-out 85 %,
         approach 30 %, idle 7 % of rated output), as published by the UK CAA:
         https://www.caa.co.uk/environmental-sustainability/uk-aviation-environmental-review/uk-aer-air-quality/air-quality-international-policy-and-regulation/
"""

ENGINE = "CFM56-7B26/3"
EDB_UID = "8CM065"

# --- Take-off rating, sea-level static, ISA ---------------------------------
RATED_THRUST_KN = 117.0       # [EDB] "Rated Thrust (kN)"; [TCDS] §III.6 TI take-off thrust 11699 daN = 116.99 kN
OPR_TAKEOFF = 27.7            # [EDB] "Pressure Ratio" (at take-off rating, SLS ISA per [EDBI] §4)
BPR_TAKEOFF = 5.1             # [EDB] "B/P Ratio" (at max thrust, SLS ISA per [EDBI] §4); 2 significant figures

# --- LTO fuel flows, sea-level static, uninstalled ---------------------------
# [EDB] "Fuel Flow T/O|C/O|App|Idle (kg/sec)"; thrust fractions per [LTO].
# [EDB] also records "Loads Power Extraction (kW)" = 0 and "Loads Stage Bleed CF (%)" = 0.
LTO_POINTS = (
    # (name, fraction of rated thrust, fuel flow kg/s)
    ("Take-off", 1.00, 1.213),
    ("Climb-out", 0.85, 0.986),
    ("Approach", 0.30, 0.331),
    ("Idle", 0.07, 0.108),
)

# --- Limits (for plausibility checks, not tuning targets) --------------------
MAX_CONTINUOUS_THRUST_KN = 115.21  # [TCDS] §III.6 TI max continuous, CFM56-7B26/3: 11521 daN
N1_MAX_RPM = 5382                  # [TCDS] §IV.2 LP rotor, = 104 %
N2_MAX_RPM = 15183                 # [TCDS] §IV.2 HP rotor, = 105 %
N1_100PCT_RPM = N1_MAX_RPM / 1.04  # derived: 5175 rpm
N2_100PCT_RPM = N2_MAX_RPM / 1.05  # derived: 14460 rpm
EGT_TAKEOFF_MAX_C = 950            # [TCDS] §IV.1.1 displayed EGT at station T49.5 (incl. "shunt" offsets)

# --- Acceptance tolerances (agreed with project owner, Phase 1) --------------
TOLERANCE_PCT = {
    "OPR": 3.0,
    "BPR": 5.0,
    "Take-off": 5.0,
    "Climb-out": 5.0,
    "Approach": 10.0,
    "Idle": 20.0,  # generic pyCycle maps are least accurate at low power
}

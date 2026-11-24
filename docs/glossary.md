# Glossary: 20 terms a developer needs

Each entry gives the plain meaning, a software analogy where it helps, and where
the term appears in the code. "Model variable" names are pyCycle paths, for
example `DESIGN.perf.Fn`.

---

### 1. Turbofan
A jet engine where a big front **fan** pushes most of the air *around* the engine
core (the bypass stream). Only a small part goes *through* the core, where fuel
is burned. Moving a lot of air a little is more efficient than moving a little air a
lot. Analogy: horizontal scaling (many cheap workers) instead of one very fast worker.

### 2. Station
A numbered checkpoint along the airflow where pressure, temperature and flow are
reported. 0 = free stream, 2 = fan face, 3 = compressor exit, 4 = turbine inlet,
5 = turbine exit, 8/18 = core/bypass nozzles. Analogy: logging probes between
pipeline stages. Code: every `*.Fl_O` in `viewer()`.

### 3. Spool (shaft)
A rotating shaft that connects turbines to compressors. This engine has two:
the **LP spool** (fan + booster, driven by the LPT) and the **HP spool** (HPC,
driven by the HPT). Each shaft is a shared budget: the turbine earns power,
the compressors spend it, and at steady state the budget balances. Code:
`lp_shaft`, `hp_shaft`, `LP_Nmech`, `HP_Nmech` (rpm).

### 4. Fan
The large front rotor. It makes most of the thrust by gently pushing the bypass
air. Code: `fan` (`fan_PR` ≈ 1.7).

### 5. Compressor: booster (LPC) and HPC
These squeeze the core air before burning. The booster (`lpc`) sits on the LP
spool, and the high-pressure compressor (`hpc`) on the HP spool. More squeeze
means more efficient burning. Code: `lpc_PR`, `hpc_PR`.

### 6. Combustor (burner) and fuel-air ratio (FAR)
Where fuel is burned in the compressed air. **FAR** = kg of fuel per kg of core
air (about 0.025 at cruise in our model). It acts as the throttle knob the solver turns. Code:
`burner`, `balance.FAR`.

### 7. Turbine: HPT and LPT
These extract energy from the hot gas to drive the compressors and fan. The HPT
drives the HPC, and the LPT drives the fan and booster. Code: `hpt`, `lpt`.

### 8. Nozzle
The exit duct that accelerates the gas into a jet. There are two: `core_nozz` and
`byp_nozz`. Their **throat areas** are fixed after design, and that constrains
off-design operation.

### 9. Bypass ratio (BPR)
Bypass airflow ÷ core airflow. Our model uses about 5. Modern geared turbofans
are much higher (public figures will be sourced in Phase 4). Higher BPR usually means lower fuel burn but a bigger, heavier
fan. Code: `BPR`, `splitter.BPR`.

### 10. Overall pressure ratio (OPR)
Compressor exit pressure ÷ inlet pressure (fan × booster × HPC, minus losses).
Higher OPR is more efficient but hotter and harder to build. Code: `perf.OPR`.

### 11. T4 (turbine inlet temperature)
The hottest gas temperature in the engine, at the combustor exit. It is the main
limit on power, set by what turbine blade materials and cooling can survive.
Analogy: CPU thermal limit. You can boost briefly (takeoff), but not forever.
Code: `T4_MAX`, `burner.Fl_O:tot:T`.

### 12. Thrust: net, gross, ram drag
**Gross thrust** (`Fg`) is the push from the nozzle jets. **Ram drag**
(`F_ram`) is the cost of slowing incoming air to engine speed. **Net thrust**
`Fn = Fg − F_ram` is what actually pushes the aircraft. Code: `perf.Fn`.

### 13. TSFC (thrust-specific fuel consumption)
Fuel flow ÷ net thrust. It is the engine's efficiency metric (lower is better),
like "watts per request". US: lbm/(lbf·h). SI: g/(kN·s) (multiply by 28.33).
Code: `perf.TSFC`.

### 14. Mass flow (W)
kg/s (or lbm/s) of air entering the engine. It sets engine size: thrust scales
roughly with airflow. Code: `inlet.Fl_O:stat:W`, `balance.W`.

### 15. Total vs static properties
**Static** = what a thermometer moving *with* the air reads. **Total** (stagnation)
= what you'd read if you brought the air to rest, which adds its kinetic energy.
Engine calculations mostly use totals (`tot:P`, `tot:T`). Analogy: balance vs
balance including pending credits.

### 16. Isentropic efficiency
How close a compressor or turbine comes to an ideal, loss-free process (1.0 =
perfect). Our model uses 0.87 to 0.92. Code: `fan_eff`, `hpc_eff`, `hpt_eff`, ...

### 17. Design point vs off-design (and flight condition)
**Design point**: the single condition at which you *size* the hardware (here:
cruise, Mach 0.8, 35,000 ft, standard-day **ISA** atmosphere). **Off-design**:
any other condition, run on the now-fixed hardware. Analogy: choosing instance
size, then load-testing it. Code: `DESIGN` vs `OD_max`, `OD_part`. Details in
[architecture.md](architecture.md#2b-balances-the-constraints).

### 18. Component map (R-line, corrected flow/speed)
A lookup table describing how a compressor or turbine behaves away from its
design point: given speed and position on the map (`RlineMap`), it returns
pressure ratio, efficiency and flow. "Corrected" values normalise for inlet
temperature and pressure so one table covers all altitudes. Analogy: a
performance profile curve for a service. pyCycle ships generic maps (`pyc.FanMap`, ...)
and scales them to our design.

### 19. Bleed, cooling air, power extraction
Air taken from the compressor for other jobs: **cooling** the turbines
(`cool1..4`, returned downstream) and **customer bleed** for cabin air
(`cust`, lost from the cycle). **Power extraction** (`HPX`) is shaft power taken
by aircraft generators and pumps. Both are overheads that cost fuel, like
background jobs consuming CPU.

### 20. Rating (takeoff, climb, max continuous, cruise)
A certified power setting with its own limits. Takeoff allows the highest T4,
for a few minutes. The **certified thrust** quoted for an engine is its sea-level
static takeoff rating, as listed in the Type Certificate Data Sheet and the ICAO
databank (we'll pull the CFM56-7B26 figure from those in Phase 1). Engines are often
**flat-rated**: they give the same takeoff thrust up to a certain hot-day
temperature. Our model has no separate takeoff rating yet (Phase 1).

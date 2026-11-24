# Open-source tools and licences

Licences are checked from the installed package's licence file or the
repository's LICENSE before use.

| Tool | Used for | Version | Licence | How checked | Since |
|---|---|---|---|---|---|
| [OpenMDAO](https://github.com/OpenMDAO/OpenMDAO) | Solver and optimisation framework | 3.45.2 | Apache 2.0 | `openmdao-3.45.2.dist-info/licenses/LICENSE.txt`, METADATA `License-Expression: Apache-2.0` | Phase 0 |
| [pyCycle](https://github.com/OpenMDAO/pyCycle) | Engine cycle (thermodynamic) model | git `ee7e161` (4.4.1.dev0) | Apache 2.0 | `om_pycycle-4.4.1.dev0.dist-info/licenses/LICENSE.txt` | Phase 0 |
| [NumPy](https://github.com/numpy/numpy) | Numerics (OpenMDAO dependency) | 2.5.5 | BSD-3-Clause | Well known; not re-checked | Phase 0 |
| [pytest](https://github.com/pytest-dev/pytest) | Tests (development only) | latest | MIT | Well known; not re-checked | Phase 0 |

## Planned (licence to be checked when the phase starts)
Streamlit, matplotlib or plotly (Phase 2); CadQuery, ParaBlade, Gmsh, SU2,
CalculiX (Phase 5); Cantera (if combustion detail is needed).

## Environment
Python 3.12 in `.venv`. Python 3.14 is installed on this machine but has not been
tested with pyCycle.

# Reference data

Raw public source files are **downloaded locally, not committed** (they are © EASA/ICAO;
EASA permits reproduction with acknowledgement "save where otherwise stated", and the
TCDS is marked "All rights reserved", so we keep the repo to extracted values + citations).

```
python data/fetch_reference_data.py
```

| File | Source | Issue | Accessed |
|---|---|---|---|
| `icao_edb/edb-emissions-databank_v32B.xlsx` | [ICAO Aircraft Engine Emissions Databank (EASA)](https://www.easa.europa.eu/en/domains/environment/icao-aircraft-engine-emissions-databank) | v32B, 11/2026 | 2026-11-24 |
| `icao_edb/edb-introduction_text-rev3.pdf` | same page, "Introduction to the ICAO Engine Emissions Databank" | rev3, 11/2026 | 2026-11-24 |
| `easa_tcds/EASA_TCDS_E.004_CFM56-7B.pdf` | [EASA TCDS E.004, CFM56-7B series](https://www.easa.europa.eu/en/document-library/type-certificates/engine-cs-e/easae004-cfm-international-sa-cfm56-7b-series) | issue 07, 2023-01-09 | 2026-11-24 |

The extracted numbers, with exact row/section citations, are in `../reference_data.py`.

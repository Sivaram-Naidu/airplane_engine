"""Download the public source files behind reference_data.py (not redistributed in git).

Usage: python data/fetch_reference_data.py
"""
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = {
    "icao_edb/edb-emissions-databank_v32B.xlsx": "https://www.easa.europa.eu/en/downloads/131424/en",
    "icao_edb/edb-introduction_text-rev3.pdf": "https://www.easa.europa.eu/en/downloads/45576/en",
    "easa_tcds/EASA_TCDS_E.004_CFM56-7B.pdf": "https://www.easa.europa.eu/en/downloads/7795/en",
}

for rel, url in FILES.items():
    dest = os.path.join(HERE, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
        f.write(r.read())
    print(f"{rel}: {os.path.getsize(dest)} bytes")
print("Note: EASA may publish newer issues at the same links; reference_data.py cites v32B / TCDS issue 07.")

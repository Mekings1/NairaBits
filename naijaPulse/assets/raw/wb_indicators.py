""" @bruin
name: raw.wb_indicators
type: python
connection: duckdb-default
materialization:
    type: table
description: |
    Pulls five macroeconomic indicators from the World Bank Open Data API
    for ten African countries: GDP growth, inflation, FDI as % of GDP,
    electricity access, and unemployment. Covers the last ten available
    years per country.
tags:
  - macroeconomics
  - world-bank
  - africa
  - raw
@bruin """

import requests
import pandas as pd

def materialize():
    indicators = {
        "NY.GDP.MKTP.KD.ZG": "gdp_growth",
        "FP.CPI.TOTL.ZG": "inflation",
        "BX.KLT.DINV.WD.GD.ZS": "fdi_pct_gdp",
        "EG.ELC.ACCS.ZS": "electricity_access",
        "SL.UEM.TOTL.ZS": "unemployment"
    }
    countries = "NG;KE;ZA;GH;EG;ET;TZ;UG;RW;SN"
    rows = []

    for code, name in indicators.items():
        url = (
            f"https://api.worldbank.org/v2/country/{countries}"
            f"/indicator/{code}?format=json&per_page=500&mrv=10"
        )
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if not isinstance(data, list) or len(data) < 2 or data[1] is None:
                continue

            for entry in data[1]:
                if not entry or entry.get("value") is None:
                    continue
                rows.append({
                    "country_code": str(entry.get("countryiso3code", "")),
                    "country_name": str(entry.get("country", {}).get("value", "")),
                    "indicator_name": name,
                    "year": int(entry["date"]),
                    "value": float(entry["value"])
                })
        except Exception as e:
            print(f"Warning: skipping {name} — {e}")
            continue

    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} rows across {df['indicator_name'].nunique()} indicators")
    return df

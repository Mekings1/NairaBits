""" @bruin
name: raw.exchange_rates
type: python
connection: duckdb-default
materialization:
    type: table
description: |
    Ingests daily USD exchange rates for five major African currencies
    (NGN, KES, ZAR, GHS, EGP) from the Frankfurter API covering the
    last 10 years. Serves as the foundation for currency volatility
    and purchasing power analysis across the continent.
tags:
  - currency
  - africa
  - raw
  - frankfurter
@bruin """

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def materialize():
    currencies = {
        "NGN": "USDNGN=X",
        "KES": "USDKES=X",
        "ZAR": "USDZAR=X",
        "GHS": "USDGHS=X",
        "EGP": "USDEGP=X"
    }

    end   = datetime.today().strftime("%Y-%m-%d")
    start = (datetime.today() - timedelta(days=365 * 10)).strftime("%Y-%m-%d")

    frames = []
    for currency, ticker in currencies.items():
        data = yf.download(ticker, start=start, end=end,
                           auto_adjust=True, progress=False)

        if data.empty:
            print(f"Warning: no data returned for {currency}")
            continue

        # Newer yfinance returns MultiIndex columns e.g. ("Close", "USDNGN=X")
        # Flatten to single level so we get plain "Close", "Open" etc.
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        # Date is always in the index — no need to reset_index at all
        # Build a clean DataFrame directly from the index and Close column
        currency_df = pd.DataFrame({
            "date":            data.index.strftime("%Y-%m-%d"),
            "base_currency":   "USD",
            "target_currency": currency,
            "rate":            data["Close"].astype(float).values
        })

        frames.append(currency_df)
        print(f"Loaded {len(currency_df)} rows for {currency}")

    if not frames:
        print("Warning: no data was processed for any currency")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    print(f"Total: {len(df)} rows across {df['target_currency'].nunique()} currencies")
    return df

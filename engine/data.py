"""
Data layer. Single interface for fetching OHLCV data from
Yahoo Finance (backtest) or Kite (live).
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def fetch_ohlcv(ticker, years=3, source="yahoo"):
    if source == "yahoo":
        return _fetch_yahoo(ticker, years)
    raise ValueError(f"Unknown source: {source}")


def _fetch_yahoo(ticker, years):
    end = datetime.now()
    start = end - timedelta(days=years * 365)
    suffix = "" if "." in ticker else ".NS"
    symbol = ticker + suffix

    df = yf.download(symbol, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), progress=False)
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel("Ticker")
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    if len(df) < 201:
        return None
    return df

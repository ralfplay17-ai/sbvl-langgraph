import pandas as pd
import numpy as np


def wilder_rsi(close: pd.Series, periodo: int = 14) -> pd.Series:
    p = close[close > 0].dropna()
    if len(p) < periodo + 2:
        return pd.Series([float("nan")] * len(close), index=close.index)
    delta = p.diff()
    avg_gain = delta.clip(lower=0).ewm(alpha=1.0 / periodo, min_periods=periodo, adjust=False).mean()
    avg_loss = (-delta.clip(upper=0)).ewm(alpha=1.0 / periodo, min_periods=periodo, adjust=False).mean()
    rs = avg_gain / avg_loss.clip(lower=1e-10)
    return (100 - (100 / (1 + rs))).clip(0, 100).reindex(close.index)


def calcular_indicadores(close: pd.Series) -> list[dict]:
    close = close[close > 0].dropna()
    rsi = wilder_rsi(close)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean() if len(close) >= 50 else None

    rows = []
    for dt, precio in close.items():
        def _v(s, _dt=dt):
            if s is None or _dt not in s.index:
                return None
            v = s.loc[_dt]
            return None if pd.isna(v) else float(v)
        rows.append({
            "fecha":  dt.strftime("%Y-%m-%d"),
            "close":  float(precio),
            "open":   float(precio),
            "high":   float(precio),
            "low":    float(precio),
            "rsi":    _v(rsi),
            "macd":   _v(macd),
            "signal": _v(signal),
            "sma20":  _v(sma20),
            "sma50":  _v(sma50),
        })
    return rows


def calcular_indicadores_ohlc(df: pd.DataFrame) -> list[dict]:
    """Versión con OHLC completo para candlestick."""
    close = df["Close"][df["Close"] > 0].dropna()
    rsi = wilder_rsi(close)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean() if len(close) >= 50 else None

    rows = []
    for dt in close.index:
        def _v(s, _dt=dt):
            if s is None or _dt not in s.index:
                return None
            v = s.loc[_dt]
            return None if pd.isna(v) else float(v)

        row = df.loc[dt] if dt in df.index else None
        rows.append({
            "fecha":  dt.strftime("%Y-%m-%d"),
            "open":   float(row["Open"])  if row is not None and not pd.isna(row["Open"])  else float(close.loc[dt]),
            "high":   float(row["High"])  if row is not None and not pd.isna(row["High"])  else float(close.loc[dt]),
            "low":    float(row["Low"])   if row is not None and not pd.isna(row["Low"])   else float(close.loc[dt]),
            "close":  float(close.loc[dt]),
            "volume": int(row["Volume"]) if row is not None and not pd.isna(row.get("Volume", float("nan"))) else None,
            "rsi":    _v(rsi),
            "macd":   _v(macd),
            "signal": _v(signal),
            "sma20":  _v(sma20),
            "sma50":  _v(sma50),
        })
    return rows

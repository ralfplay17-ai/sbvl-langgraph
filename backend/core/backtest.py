import pandas as pd
from core.indicators import wilder_rsi


def _download(symbol: str, **kwargs):
    import yfinance as yf
    import pandas as pd
    try:
        data = yf.download(symbol, progress=False, auto_adjust=True, **kwargs)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if not data.empty:
            closes = data["Close"]
            if hasattr(closes, "squeeze"):
                closes = closes.squeeze()
            data["Close"] = closes
            return data
    except Exception:
        pass
    return pd.DataFrame()


def _download_td(symbol: str, outputsize: int = 365) -> "pd.DataFrame":
    import pandas as pd
    import requests
    from config import get_settings
    td_key = get_settings().twelvedata_key
    if not td_key:
        return pd.DataFrame()
    try:
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={"symbol": symbol, "interval": "1day",
                    "outputsize": outputsize, "apikey": td_key},
            timeout=20,
        )
        values = r.json().get("values", [])
        if not values:
            return pd.DataFrame()
        values = list(reversed(values))
        df = pd.DataFrame(values)
        df.index = pd.to_datetime(df["datetime"])
        df = df.drop(columns=["datetime"])
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df.columns = [c.capitalize() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


def _benchmark(fecha_ini, fecha_fin) -> dict:
    for sym in ("EPU", "^SPBLPGPT"):
        try:
            hist = _download(sym, start=fecha_ini, end=fecha_fin)
            if hist.empty or len(hist) < 20:
                continue
            closes = hist["Close"].dropna()
            rets = closes.pct_change().dropna()
            sharpe = float((rets.mean() / rets.std()) * (252 ** 0.5)) if rets.std() != 0 else 0.0
            return {
                "ticker": sym,
                "retorno_total": round((float(closes.iloc[-1]) - float(closes.iloc[0])) / float(closes.iloc[0]) * 100, 2),
                "sharpe_ratio": round(sharpe, 4),
            }
        except Exception:
            continue
    return {"ticker": "N/D", "retorno_total": None, "sharpe_ratio": None}


def _senal_row(row) -> str:
    if pd.isna(row["RSI"]) or pd.isna(row["SMA20"]) or pd.isna(row["SMA50"]):
        return "MANTENER"
    alc = baj = 0
    if row["RSI"] < 30:
        alc += 1
    elif row["RSI"] > 70:
        baj += 1
    if row["MACD_H"] > 0:
        alc += 1
    elif row["MACD_H"] < 0:
        baj += 1
    if row["SMA20"] > row["SMA50"]:
        alc += 1
    elif row["SMA20"] < row["SMA50"]:
        baj += 1
    return "COMPRAR" if alc > baj else ("VENDER" if baj > alc else "MANTENER")


def ejecutar_backtest(ticker: str, dias: int) -> dict:
    try:
        hist = _download(ticker, period=f"{dias}d")
        if hist.empty:
            hist = _download_td(ticker, outputsize=min(dias + 30, 500))

        if hist.empty:
            return {"error": f"Sin datos para {ticker}"}

        cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in hist.columns]
        df = hist[cols].copy()
        if "Close" not in df.columns:
            return {"error": f"Sin datos de cierre para {ticker}"}
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df.sort_index().tail(dias)

        if len(df) < 20:
            return {"error": "Datos insuficientes"}

        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        macd  = ema12 - ema26
        df = df.assign(
            RSI    = wilder_rsi(df["Close"]),
            MACD   = macd,
            Signal = macd.ewm(span=9, adjust=False).mean(),
            MACD_H = macd - macd.ewm(span=9, adjust=False).mean(),
            SMA20  = df["Close"].rolling(20).mean(),
            SMA50  = df["Close"].rolling(50).mean(),
        )
        df["Senal"] = df.apply(_senal_row, axis=1)

        capital = 10_000.0
        posicion = 0.0
        ops: list[dict] = []
        hist_cap: list[dict] = []

        for fecha, row in df.iterrows():
            precio = row["Close"]
            if row["Senal"] == "COMPRAR" and posicion == 0:
                posicion = capital / precio
                capital = 0.0
                ops.append({"fecha": fecha.strftime("%Y-%m-%d"), "tipo": "COMPRA", "precio": float(precio)})
            elif row["Senal"] == "VENDER" and posicion > 0:
                capital = posicion * precio
                ops.append({"fecha": fecha.strftime("%Y-%m-%d"), "tipo": "VENTA",
                            "precio": float(precio), "ganancia": float(capital - 10_000)})
                posicion = 0.0
            hist_cap.append({"fecha": fecha.strftime("%Y-%m-%d"),
                             "capital": float(posicion * precio if posicion > 0 else capital)})

        if posicion > 0:
            capital = posicion * float(df["Close"].iloc[-1])

        caps = [h["capital"] for h in hist_cap]
        ret_pso = (caps[-1] - 10_000) / 10_000 * 100
        rets_d  = pd.Series(caps).pct_change().dropna()
        sharpe  = float((rets_d.mean() / rets_d.std()) * (252 ** 0.5)) if rets_d.std() != 0 else 0.0
        cummax  = pd.Series(caps).cummax()
        mdd     = float(((pd.Series(caps) - cummax) / cummax).min() * 100)
        cerradas = [o for o in ops if "ganancia" in o]
        win_rate = len([o for o in cerradas if o["ganancia"] > 0]) / len(cerradas) * 100 if cerradas else 0.0

        pi = float(df["Close"].iloc[0])
        pf = float(df["Close"].iloc[-1])
        ret_bh = (pf - pi) / pi * 100
        hist_bh = [{"fecha": df.index[i].strftime("%Y-%m-%d"),
                    "capital": float(10_000 * df["Close"].iloc[i] / pi)} for i in range(len(df))]

        return {
            "ticker": ticker,
            "periodo": {
                "inicio": df.index[0].strftime("%Y-%m-%d"),
                "fin": df.index[-1].strftime("%Y-%m-%d"),
                "dias": len(df),
            },
            "estrategia_pso": {
                "capital_final": round(caps[-1], 2),
                "retorno_total": round(ret_pso, 2),
                "sharpe_ratio": round(sharpe, 4),
                "max_drawdown": round(mdd, 2),
                "win_rate": round(win_rate, 1),
                "num_operaciones": len(cerradas),
                "historial_capital": hist_cap,
            },
            "buy_hold": {
                "capital_final": round(10_000 * (1 + ret_bh / 100), 2),
                "retorno_total": round(ret_bh, 2),
                "historial_capital": hist_bh,
            },
            "comparacion": {
                "diferencia": round(ret_pso - ret_bh, 2),
                "ganador": "PSO" if caps[-1] > 10_000 * (1 + ret_bh / 100) else "Buy & Hold",
            },
            "benchmark": _benchmark(df.index[0], df.index[-1]),
            "operaciones": ops,
        }
    except Exception as e:
        return {"error": str(e)}

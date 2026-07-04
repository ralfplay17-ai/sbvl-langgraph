import json
import requests
import yfinance as yf
from langchain_core.tools import tool


def _closes_yf(symbol: str):
    try:
        data = yf.download(symbol, period="20d", progress=False, auto_adjust=True)
        if data.empty or len(data) < 2:
            return None
        closes = data["Close"]
        if hasattr(closes, "squeeze"):
            closes = closes.squeeze()
        closes = closes.dropna()
        return closes if len(closes) >= 2 else None
    except Exception:
        return None


def _closes_av_fx(from_sym: str, av_key: str):
    try:
        import pandas as pd
        r = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "FX_DAILY", "from_symbol": from_sym,
                    "to_symbol": "USD", "outputsize": "compact", "apikey": av_key},
            timeout=15,
        )
        series = r.json().get("Time Series FX (Daily)", {})
        if not series:
            return None
        dates = sorted(series.keys())[-20:]
        closes = pd.Series(
            [float(series[d]["4. close"]) for d in dates],
            index=pd.to_datetime(dates),
        )
        return closes if len(closes) >= 2 else None
    except Exception:
        return None


def _closes_twelvedata(symbol: str, td_key: str):
    try:
        import pandas as pd
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={"symbol": symbol, "interval": "1day",
                    "outputsize": 20, "apikey": td_key},
            timeout=15,
        )
        values = r.json().get("values", [])
        if not values:
            return None
        values = list(reversed(values))
        closes = pd.Series(
            [float(v["close"]) for v in values],
            index=pd.to_datetime([v["datetime"] for v in values]),
        )
        return closes if len(closes) >= 2 else None
    except Exception:
        return None


@tool
def obtener_datos_commodities(ticker: str) -> str:
    """
    Obtiene precios actuales de metales (Oro, Plata, Cobre) relevantes para mineras BVL.
    Devuelve precio, cambio diario % y tendencia 5 días.
    Fuentes: yfinance → Alpha Vantage → Twelve Data (ETF proxy).
    Input: ticker de la acción (contextualiza el análisis, siempre devuelve los 3 metales).
    """
    from config import get_settings
    s = get_settings()
    av_key = s.alpha_vantage_key
    td_key = s.twelvedata_key

    # (nombre, yf_futuro, av_fx_sym, td_etf_sym, label, unit)
    metals = [
        ("Oro",   "GC=F", "XAU", "GLD",  "XAU/USD", "oz"),
        ("Plata", "SI=F", "XAG", "SLV",  "XAG/USD", "oz"),
        ("Cobre", "HG=F", None,  "COPX", "HG=F",    "lb"),
    ]
    result: dict[str, dict] = {}

    for nombre, yf_sym, av_sym, td_etf, label, unit in metals:
        closes = _closes_yf(yf_sym)

        if closes is None and av_sym and av_key:
            closes = _closes_av_fx(av_sym, av_key)

        if closes is None and td_key:
            closes = _closes_twelvedata(td_etf, td_key)

        if closes is None:
            closes = _closes_yf(td_etf)

        if closes is None or len(closes) < 2:
            result[nombre] = {"error": "Sin datos"}
            continue

        ph = float(closes.iloc[-1])
        pa = float(closes.iloc[-2])
        p5 = float(closes.iloc[-5]) if len(closes) >= 5 else float(closes.iloc[0])
        result[nombre] = {
            "label": label,
            "unit": unit,
            "precio": round(ph, 2),
            "cambio_dia_pct": round((ph - pa) / pa * 100, 2),
            "tendencia_5d_pct": round((ph - p5) / p5 * 100, 2),
            "fuente": "yfinance/alphavantage/twelvedata",
        }

    return json.dumps({"ticker_referencia": ticker, "commodities": result}, ensure_ascii=False)

import json
import requests
import yfinance as yf
from langchain_core.tools import tool


def _closes_yf(symbol: str):
    try:
        import pandas as pd
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


@tool
def obtener_datos_commodities(ticker: str) -> str:
    """
    Obtiene precios actuales de metales (Oro, Plata, Cobre) relevantes para mineras BVL.
    Devuelve precio, cambio diario % y tendencia 5 días. Fuentes: yfinance con fallback Alpha Vantage.
    Input: ticker de la acción (se usa para contextualizar, siempre devuelve los 3 metales).
    """
    from config import get_settings
    av_key = get_settings().alpha_vantage_key

    metals = [
        ("Oro",   "GC=F", "XAU", "XAU/USD", "oz"),
        ("Plata", "SI=F", "XAG", "XAG/USD", "oz"),
        ("Cobre", "HG=F", None,  "HG=F",    "lb"),
    ]
    result: dict[str, dict] = {}

    for nombre, symbol, av_sym, label, unit in metals:
        closes = _closes_yf(symbol)

        if closes is None and av_sym and av_key:
            closes = _closes_av_fx(av_sym, av_key)

        if closes is None and symbol == "HG=F":
            closes = _closes_yf("COPX")

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
            "fuente": "yfinance/alphavantage",
        }

    return json.dumps({"ticker_referencia": ticker, "commodities": result}, ensure_ascii=False)

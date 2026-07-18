import json
from langchain_core.tools import tool
from core.price_sources import METALS, closes_con_fallback


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

    result: dict[str, dict] = {}

    for nombre, yf_sym, av_sym, td_etf, label, unit in METALS:
        closes = closes_con_fallback(yf_sym, av_sym, td_etf, av_key, td_key)

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

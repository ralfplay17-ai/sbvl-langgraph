import json
from langchain_core.tools import tool


@tool
def obtener_datos_commodities(ticker: str) -> str:
    """
    Obtiene precios actuales de metales (Oro, Plata, Cobre) relevantes para mineras BVL.
    Devuelve precio, cambio diario % y tendencia 5 días. Fuente: yfinance.
    Input: ticker de la acción (se usa para contextualizar, siempre devuelve los 3 metales).
    """
    import yfinance as yf

    metals = [
        ("Oro",   "GC=F", "XAU/USD", "oz"),
        ("Plata", "SI=F", "XAG/USD", "oz"),
        ("Cobre", "HG=F", "HG=F",    "lb"),
    ]
    result: dict[str, dict] = {}

    for nombre, symbol, label, unit in metals:
        try:
            hist = yf.Ticker(symbol).history(period="15d")
            if hist.empty or len(hist) < 2:
                result[nombre] = {"error": "Sin datos"}
                continue
            closes = hist["Close"].dropna()
            ph = float(closes.iloc[-1])
            pa = float(closes.iloc[-2])
            p5 = float(closes.iloc[-5]) if len(closes) >= 5 else float(closes.iloc[0])
            result[nombre] = {
                "label": label,
                "unit": unit,
                "precio": round(ph, 2),
                "cambio_dia_pct": round((ph - pa) / pa * 100, 2),
                "tendencia_5d_pct": round((ph - p5) / p5 * 100, 2),
                "fuente": "yfinance",
            }
        except Exception as e:
            result[nombre] = {"error": str(e)}

    return json.dumps({"ticker_referencia": ticker, "commodities": result}, ensure_ascii=False)

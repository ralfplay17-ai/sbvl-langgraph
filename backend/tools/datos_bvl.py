import requests
import pandas as pd
import json
import os
from datetime import date, timedelta
from langchain_core.tools import Tool

TICKER_MAP = {
    "BVN": "BUENAVC1",
    "SCCO": "SCCO",
}

BVL_API_BASE = "https://dataondemand.bvl.com.pe/v1"
BVL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bvl.com.pe/",
    "Origin": "https://www.bvl.com.pe",
}


def _calcular_rsi(precios: pd.Series, periodo: int = 14) -> pd.Series:
    delta = precios.diff()
    ganancia = delta.where(delta > 0, 0).rolling(window=periodo).mean()
    perdida = -delta.where(delta < 0, 0).rolling(window=periodo).mean()
    return 100 - (100 / (1 + ganancia / perdida))


def _calcular_indicadores(close: pd.Series, nemonico: str, ticker: str) -> dict:
    rsi = _calcular_rsi(close)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist_v = macd - signal
    sma20 = close.rolling(window=20).mean()
    sma50 = close.rolling(window=50).mean() if len(close) >= 50 else None

    precio_actual = float(close.iloc[-1])
    precio_anterior = float(close.iloc[-2]) if len(close) > 1 else precio_actual
    cambio_pct = (precio_actual - precio_anterior) / precio_anterior * 100

    rsi_actual = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    rsi_zona = "sobrecompra" if rsi_actual >= 70 else ("sobreventa" if rsi_actual <= 30 else "neutral")
    sma20_v = float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else None
    sma50_v = float(sma50.iloc[-1]) if sma50 is not None and not pd.isna(sma50.iloc[-1]) else None
    tendencia = ("alcista" if sma20_v and sma50_v and sma20_v > sma50_v else "bajista") if sma50_v else "indeterminada"
    macd_v = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0.0
    signal_v = float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else 0.0
    hist_vv = float(hist_v.iloc[-1]) if not pd.isna(hist_v.iloc[-1]) else 0.0

    cambio_5d_pct = None
    if len(close) >= 6:
        p5 = float(close.iloc[-6])
        if p5 != 0:
            cambio_5d_pct = round((precio_actual - p5) / p5 * 100, 2)

    return {
        "ticker": ticker.upper(),
        "nemonico_bvl": nemonico,
        "precio_actual": precio_actual,
        "cambio_pct": round(cambio_pct, 2),
        "cambio_5d_pct": cambio_5d_pct,
        "RSI": round(rsi_actual, 2),
        "RSI_zona": rsi_zona,
        "MACD": round(macd_v, 4),
        "MACD_signal": round(signal_v, 4),
        "MACD_hist": round(hist_vv, 4),
        "SMA20": round(sma20_v, 2) if sma20_v else None,
        "SMA50": round(sma50_v, 2) if sma50_v else None,
        "tendencia": tendencia,
        "fuente": "BVL",
    }


def _cargar_desde_bvl_api(ticker: str) -> dict | None:
    nemonico = TICKER_MAP.get(ticker.upper())
    if not nemonico:
        return None
    try:
        fecha_fin = date.today()
        fecha_ini = fecha_fin - timedelta(days=120)
        r = requests.get(
            BVL_API_BASE + "/stock-quote/share-value",
            headers=BVL_HEADERS,
            params={"name": nemonico, "startDate": fecha_ini.isoformat(), "endDate": fecha_fin.isoformat()},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        values = data.get("values", [])
        if len(values) < 20:
            return None
        fechas = [v[0] for v in values]
        cierres = [float(v[1]) for v in values]
        close = pd.Series(cierres, index=pd.to_datetime(fechas)).sort_index()
        return _calcular_indicadores(close, nemonico, ticker)
    except Exception:
        return None


def _cargar_desde_alpha_vantage(ticker: str, api_key: str) -> dict | None:
    if not api_key:
        return None
    try:
        url = (
            "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
            f"&symbol={ticker}&outputsize=compact&apikey={api_key}"
        )
        resp_data = requests.get(url, timeout=20).json()
        if "Time Series (Daily)" not in resp_data:
            return None
        ts = resp_data["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(ts, orient="index").astype(float)
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        df.index = pd.to_datetime(df.index)
        close = df.sort_index().tail(60)["Close"]
        result = _calcular_indicadores(close, TICKER_MAP.get(ticker.upper(), ticker), ticker)
        result["fuente"] = "Alpha Vantage"
        return result
    except Exception:
        return None


def build_datos_bvl_tool(api_key: str = "") -> Tool:
    av_key = api_key or os.environ.get("ALPHA_VANTAGE_KEY", "")

    def obtener_datos(input_text: str = "") -> str:
        text_lower = input_text.lower()
        ticker = "SCCO" if ("scco" in text_lower or "southern" in text_lower or "cobre" in text_lower) else "BVN"

        data = _cargar_desde_bvl_api(ticker)
        if data is None:
            data = _cargar_desde_alpha_vantage(ticker, av_key)

        if data is None:
            return json.dumps({"error": "No se pudieron obtener datos de BVL ni Alpha Vantage"})
        return json.dumps(data, ensure_ascii=False)

    return Tool(
        name="obtener_datos_bvl",
        description=(
            "Obtiene precio, indicadores tecnicos (RSI, MACD, SMA20, SMA50) y tendencia "
            "para acciones BVL. Input: ticker o empresa (BVN, SCCO, Buenaventura, Southern Copper). "
            "SIEMPRE llama esta herramienta antes de analizar."
        ),
        func=obtener_datos,
    )

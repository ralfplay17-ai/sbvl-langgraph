import json
import os
import requests
import pandas as pd
from datetime import date, timedelta
from langchain_core.tools import tool
from core.indicators import wilder_rsi

BVL_API_BASE = "https://dataondemand.bvl.com.pe/v1"
BVL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bvl.com.pe/",
    "Origin": "https://www.bvl.com.pe",
}

TICKER_MAP: dict[str, str] = {
    "BVN": "BUENAVC1", "BUENAVC1": "BUENAVC1", "BUENAVENTURA": "BUENAVC1",
    "SCCO": "SCCO", "SOUTHERN": "SCCO", "SOUTHERNCOPPER": "SCCO",
    "CVERDEC1": "CVERDEC1", "CERROVERDE": "CVERDEC1",
    "MINSURI1": "MINSURI1", "MINSUR": "MINSURI1",
    "VOLCABC1": "VOLCABC1", "VOLCAN": "VOLCABC1",
    "ATACOBC1": "ATACOBC1", "ATACOCHA": "ATACOBC1",
    "NEXAPEC1": "NEXAPEC1", "NEXA": "NEXAPEC1",
    "BROCALC1": "BROCALC1", "BROCAL": "BROCALC1",
    "SHPC1": "SHPC1", "SHOUGANG": "SHPC1",
    "PODERC1": "PODERC1", "PODEROSA": "PODERC1",
    "MOROCOC1": "MOROCOC1", "MOROCOCHA": "MOROCOC1",
    "LUISAI1": "LUISAI1", "MINCORC1": "MINCORC1",
    "PERUBAI1": "PERUBAI1", "FOSPACC1": "FOSPACC1",
    "CASTROC1": "CASTROC1",
}

AV_TICKER_MAP: dict[str, str] = {
    "BUENAVC1": "BVN",    # Buenaventura — ADR propio en NYSE
    "SCCO": "SCCO",       # Southern Copper — cotiza directo en NYSE
    "NEXAPEC1": "NEXA",   # Nexa Resources Perú — proxy: ADR de la matriz Nexa Resources S.A. (NYSE)
}
# El resto de nemónicos (CVERDEC1, MINSURI1, VOLCABC1, ATACOBC1, BROCALC1, SHPC1,
# PODERC1, MOROCOC1, LUISAI1, MINCORC1, PERUBAI1, FOSPACC1, CASTROC1) solo cotizan
# en la BVL y no tienen ADR ni listado en EEUU, por lo que no existe símbolo válido
# en Alpha Vantage para ellos.


def _detectar_nemonico(text: str) -> str:
    upper = text.upper().strip()
    for key in sorted(TICKER_MAP.keys(), key=len, reverse=True):
        if key in upper:
            return TICKER_MAP[key]
    return "BUENAVC1"


def _f(v):
    try:
        return float(v) if v not in (None, "", "-", "0") else None
    except Exception:
        return None


def _precio_rt(nemonico: str) -> dict | None:
    try:
        r = requests.get(BVL_API_BASE + "/issuers", headers=BVL_HEADERS, timeout=15)
        r.raise_for_status()
        company_code = next(
            (x["companyCode"] for x in r.json() if x.get("tkrCode") == nemonico and x.get("active", True)),
            None
        )
        if not company_code:
            return None
        r2 = requests.get(BVL_API_BASE + f"/issuers/{company_code}/value", headers=BVL_HEADERS, timeout=15)
        r2.raise_for_status()
        for emisor in r2.json():
            for lv in emisor.get("listLastValue", []):
                if lv.get("tkrCode") == nemonico:
                    return {
                        "precio": _f(lv.get("close") or lv.get("last")),
                        "variacion_pct": _f(lv.get("var")),
                        "volumen": int(float(lv["quantityNegotiated"])) if lv.get("quantityNegotiated") else None,
                        "moneda": (lv.get("coin") or "S/.").strip(),
                    }
    except Exception:
        return None
    return None


def _cargar_serie(nemonico: str, av_key: str) -> pd.Series | None:
    # 1. CSV local
    data_dir = os.environ.get("BVL_DATA_DIR", "")
    csv_path = os.path.join(data_dir, "bvl_historico.csv") if data_dir else ""
    if csv_path and os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
            sub = df[df["nemonico"] == nemonico].copy()
            if not sub.empty:
                sub["fecha"] = pd.to_datetime(sub["fecha"])
                sub["cierre"] = pd.to_numeric(sub["cierre"], errors="coerce")
                sub = sub.sort_values("fecha").tail(60).dropna(subset=["cierre"])
                if len(sub) >= 20:
                    return pd.Series(sub["cierre"].values, index=pd.to_datetime(sub["fecha"].values))
        except Exception:
            pass

    # 2. BVL API
    try:
        fin = date.today()
        ini = fin - timedelta(days=120)
        r = requests.get(
            BVL_API_BASE + "/stock-quote/share-value",
            headers=BVL_HEADERS,
            params={"name": nemonico, "startDate": ini.isoformat(), "endDate": fin.isoformat()},
            timeout=15,
        )
        r.raise_for_status()
        values = r.json().get("values", [])
        if len(values) >= 20:
            s = pd.Series(
                [float(v[1]) for v in values],
                index=pd.to_datetime([v[0] for v in values]),
            ).sort_index()
            s = s[s > 0].dropna()
            if len(s) >= 20:
                return s
    except Exception:
        pass

    # 3. Alpha Vantage (solo si el nemónico tiene un símbolo válido mapeado)
    av_sym = AV_TICKER_MAP.get(nemonico)
    if av_key and av_sym:
        try:
            r = requests.get(
                f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
                f"&symbol={av_sym}&outputsize=compact&apikey={av_key}",
                timeout=20,
            )
            ts = r.json().get("Time Series (Daily)", {})
            if ts:
                df = pd.DataFrame.from_dict(ts, orient="index").astype(float)
                df.columns = ["Open", "High", "Low", "Close", "Volume"]
                df.index = pd.to_datetime(df.index)
                return df.sort_index().tail(60)["Close"]
        except Exception:
            pass
    return None


def _indicadores(close: pd.Series, nemonico: str, ticker_input: str, fuente: str, rt: dict | None) -> dict:
    rsi    = wilder_rsi(close)
    ema12  = close.ewm(span=12, adjust=False).mean()
    ema26  = close.ewm(span=26, adjust=False).mean()
    macd   = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    sma20  = close.rolling(20).mean()
    sma50  = close.rolling(50).mean() if len(close) >= 50 else None

    if rt and rt.get("precio"):
        precio    = rt["precio"]
        var_pct   = rt.get("variacion_pct") or 0.0
        moneda    = rt.get("moneda", "S/.")
        fuente_p  = "BVL Tiempo Real"
    else:
        precio   = float(close.iloc[-1])
        precio_a = float(close.iloc[-2]) if len(close) > 1 else precio
        var_pct  = (precio - precio_a) / precio_a * 100 if precio_a else 0
        moneda   = "S/."
        fuente_p = fuente

    rsi_v   = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    macd_v  = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0.0
    sig_v   = float(signal.iloc[-1]) if not pd.isna(signal.iloc[-1]) else 0.0
    sma20_v = float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else None
    sma50_v = float(sma50.iloc[-1]) if sma50 is not None and not pd.isna(sma50.iloc[-1]) else None

    cambio_5d = None
    if len(close) >= 6:
        p5 = float(close.iloc[-6])
        if p5:
            cambio_5d = round((precio - p5) / p5 * 100, 2)

    return {
        "ticker": ticker_input.upper(),
        "nemonico_bvl": nemonico,
        "precio_actual": round(precio, 4),
        "variacion_pct": round(var_pct, 2),
        "moneda": moneda,
        "cambio_5d_pct": cambio_5d,
        "RSI": round(rsi_v, 2),
        "RSI_zona": "sobrecompra" if rsi_v >= 70 else ("sobreventa" if rsi_v <= 30 else "neutral"),
        "MACD": round(macd_v, 4),
        "MACD_signal": round(sig_v, 4),
        "MACD_hist": round(macd_v - sig_v, 4),
        "SMA20": round(sma20_v, 2) if sma20_v else None,
        "SMA50": round(sma50_v, 2) if sma50_v else None,
        "tendencia": ("alcista" if sma20_v and sma50_v and sma20_v > sma50_v else "bajista") if sma50_v else "indeterminada",
        "fuente_indicadores": fuente,
        "fuente_precio": fuente_p,
    }


@tool
def obtener_datos_bvl(ticker: str) -> str:
    """
    Obtiene precio actual, RSI, MACD, SMA20, SMA50 y tendencia para cualquier acción minera de la BVL.
    Soporta: BVN/BUENAVC1, SCCO, CVERDEC1, MINSURI1, VOLCABC1, ATACOBC1, NEXAPEC1, BROCALC1,
    SHPC1, PODERC1, MOROCOC1, LUISAI1, MINCORC1, PERUBAI1, FOSPACC1, CASTROC1 y más.
    Input: nombre del ticker o empresa. Llama SIEMPRE antes de analizar.
    """
    from config import get_settings
    av_key = get_settings().alpha_vantage_key

    nemonico = _detectar_nemonico(ticker)
    rt = _precio_rt(nemonico)
    close = _cargar_serie(nemonico, av_key)

    if close is not None and len(close) >= 20:
        return json.dumps(_indicadores(close, nemonico, ticker, "BVL", rt), ensure_ascii=False)

    if rt and rt.get("precio"):
        return json.dumps({
            "ticker": ticker.upper(), "nemonico_bvl": nemonico,
            "precio_actual": round(rt["precio"], 4),
            "variacion_pct": round(rt.get("variacion_pct") or 0.0, 2),
            "moneda": rt.get("moneda", "S/."),
            "nota": "Sin historial suficiente para RSI/MACD/SMA",
        }, ensure_ascii=False)

    return json.dumps({"error": f"Sin datos para {nemonico}"}, ensure_ascii=False)

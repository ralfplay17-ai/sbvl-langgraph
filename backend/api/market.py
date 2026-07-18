import asyncio
import requests
import yfinance as yf
from fastapi import APIRouter
from core.indicators import calcular_indicadores_ohlc
from core.price_sources import METALS, closes_con_fallback, fetch_av_news, fetch_google_news_rss, fetch_newsapi_news

router = APIRouter()

BVL_API_BASE = "https://dataondemand.bvl.com.pe/v1"
BVL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bvl.com.pe/",
    "Origin": "https://www.bvl.com.pe",
}

TICKERS_BVL = {
    "BVN":      "BVN — Buenaventura",
    "SCCO":     "SCCO — Southern Copper",
    "CVERDEC1": "CVERDEC1 — Cerro Verde",
    "MINSURI1": "MINSURI1 — Minsur",
    "VOLCABC1": "VOLCABC1 — Volcan",
    "NEXAPEC1": "NEXAPEC1 — Nexa Resources",
    "BROCALC1": "BROCALC1 — El Brocal",
    "SHPC1":    "SHPC1 — Shougang Hierro",
    "PODERC1":  "PODERC1 — Poderosa",
    "MOROCOC1": "MOROCOC1 — Morococha",
    "LUISAI1":  "LUISAI1 — Santa Luisa",
    "ATACOBC1": "ATACOBC1 — Atacocha",
    "MINCORC1": "MINCORC1 — Cía Corona",
    "PERUBAI1": "PERUBAI1 — Perubar",
    "FOSPACC1": "FOSPACC1 — Fosfatos Pacífico",
    "CASTROC1": "CASTROC1 — Castrovirreyna",
}


@router.get("/market/tickers")
def get_tickers():
    return {"tickers": [{"value": k, "label": v} for k, v in TICKERS_BVL.items()]}


@router.get("/market/price/{ticker}")
async def get_price(ticker: str):
    def _fetch():
        try:
            r = requests.get(BVL_API_BASE + "/issuers", headers=BVL_HEADERS, timeout=10)
            r.raise_for_status()
            company_code = next(
                (x["companyCode"] for x in r.json() if x.get("tkrCode") == ticker and x.get("active", True)),
                None,
            )
            if not company_code:
                return None
            r2 = requests.get(BVL_API_BASE + f"/issuers/{company_code}/value", headers=BVL_HEADERS, timeout=10)
            r2.raise_for_status()
            for emisor in r2.json():
                for lv in emisor.get("listLastValue", []):
                    if lv.get("tkrCode") == ticker:
                        def _f(v):
                            try:
                                return float(v) if v not in (None, "", "-", "0") else None
                            except (TypeError, ValueError):
                                return None
                        return {
                            "ticker": ticker,
                            "precio": _f(lv.get("close") or lv.get("last")),
                            "variacion_pct": _f(lv.get("var")),
                            "volumen": int(float(lv["quantityNegotiated"])) if lv.get("quantityNegotiated") else None,
                            "moneda": (lv.get("coin") or "S/.").strip(),
                            "nombre": lv.get("companyName", ticker),
                        }
        except Exception:
            return None
        return None

    result = await asyncio.to_thread(_fetch)
    return result or {"ticker": ticker, "error": "No disponible"}


@router.get("/market/historico/{ticker}")
async def get_historico(ticker: str, dias: int = 60):
    def _fetch():
        import pandas as pd
        import requests as req

        # 1. yfinance
        try:
            data = yf.download(ticker, period=f"{dias}d", progress=False, auto_adjust=True)
            if not data.empty and len(data) >= 10:
                df = data.copy()
                close = df["Close"]
                if hasattr(close, "squeeze"):
                    close = close.squeeze()
                df["Close"] = close
                cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
                df = df[cols]
                df.index = pd.to_datetime(df.index).tz_localize(None)
                return calcular_indicadores_ohlc(df)
        except Exception:
            pass

        # 2. Twelve Data
        from config import get_settings
        td_key = get_settings().twelvedata_key
        if td_key:
            try:
                r = req.get(
                    "https://api.twelvedata.com/time_series",
                    params={"symbol": ticker, "interval": "1day",
                            "outputsize": dias + 30, "apikey": td_key},
                    timeout=20,
                )
                values = r.json().get("values", [])
                if values and len(values) >= 10:
                    values = list(reversed(values))
                    df = pd.DataFrame(values)
                    df.index = pd.to_datetime(df["datetime"])
                    df = df.drop(columns=["datetime"])
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    df.columns = [c.capitalize() for c in df.columns]
                    df.index = df.index.tz_localize(None)
                    return calcular_indicadores_ohlc(df)
            except Exception:
                pass

        return None

    data = await asyncio.to_thread(_fetch)
    if not data:
        return {"error": f"Sin datos históricos para {ticker}"}
    return {"ticker": ticker, "historico": data}


@router.get("/market/commodities")
async def get_commodities():
    def _fetch():
        from config import get_settings
        s = get_settings()
        av_key = s.alpha_vantage_key
        td_key = s.twelvedata_key

        result = {}
        for nombre, yf_sym, av_sym, td_etf, label, unit in METALS:
            closes = closes_con_fallback(yf_sym, av_sym, td_etf, av_key, td_key)

            if closes is None or len(closes) < 2:
                result[nombre] = {"error": "Sin datos"}
                continue

            ph = float(closes.iloc[-1])
            pa = float(closes.iloc[-2])
            p5 = float(closes.iloc[-5]) if len(closes) >= 5 else float(closes.iloc[0])
            result[nombre] = {
                "label": label, "unit": unit,
                "precio": round(ph, 2),
                "cambio_dia_pct": round((ph - pa) / pa * 100, 2),
                "tendencia_5d_pct": round((ph - p5) / p5 * 100, 2),
                "closes": [round(float(c), 2) for c in closes.tolist()],
                "dates":  [d.strftime("%d/%m") for d in closes.index],
                "fuente": "yfinance/alphavantage/twelvedata",
            }
        return result

    return await asyncio.to_thread(_fetch)


@router.get("/market/noticias/{ticker}")
async def get_noticias(ticker: str):
    from config import get_settings

    s = get_settings()
    av_key      = s.alpha_vantage_key
    newsapi_key = s.newsapi_key

    av_arts, rss_arts = await asyncio.gather(
        asyncio.to_thread(fetch_av_news, ticker, av_key),
        asyncio.to_thread(fetch_google_news_rss, ticker),
    )

    # Activar NewsAPI solo si ambas fuentes principales fallaron
    newsapi_arts: list[dict] = []
    if not av_arts and not rss_arts and newsapi_key:
        newsapi_arts = await asyncio.to_thread(fetch_newsapi_news, ticker, newsapi_key)

    return {
        "ticker": ticker,
        "alpha_vantage": av_arts,
        "google_news": rss_arts if rss_arts else newsapi_arts,
    }

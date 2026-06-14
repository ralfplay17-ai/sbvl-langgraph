import asyncio
import requests
import yfinance as yf
from fastapi import APIRouter
from core.indicators import calcular_indicadores_ohlc

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
                            try: return float(v) if v not in (None,"","-","0") else None
                            except: return None
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
        try:
            hist = yf.Ticker(ticker).history(period=f"{dias}d")
            if hist.empty or len(hist) < 10:
                return None
            import pandas as pd
            df = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
            df.index = pd.to_datetime(df.index).tz_localize(None)
            return calcular_indicadores_ohlc(df)
        except Exception:
            return None

    data = await asyncio.to_thread(_fetch)
    if not data:
        return {"error": f"Sin datos históricos para {ticker}"}
    return {"ticker": ticker, "historico": data}


@router.get("/market/commodities")
async def get_commodities():
    def _closes_yf(symbol: str):
        """Intenta obtener series de cierre desde yfinance."""
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
        """Fallback Alpha Vantage FX diario para XAU y XAG."""
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
        """Fallback Twelve Data para XAU/USD, XAG/USD, HG/USD."""
        try:
            import pandas as pd
            r = requests.get(
                "https://api.twelvedata.com/time_series",
                params={"symbol": symbol, "interval": "1day",
                        "outputsize": 20, "apikey": td_key},
                timeout=15,
            )
            data = r.json()
            values = data.get("values", [])
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

    def _fetch():
        from config import get_settings
        s = get_settings()
        av_key = s.alpha_vantage_key
        td_key = s.twelvedata_key

        # (nombre, yf_symbol, av_fx_sym, td_symbol, label, unit)
        metals = [
            ("Oro",   "GC=F", "XAU", "XAU/USD", "XAU/USD", "oz"),
            ("Plata", "SI=F", "XAG", "XAG/USD", "XAG/USD", "oz"),
            ("Cobre", "HG=F", None,  None,       "HG=F",    "lb"),
        ]
        result = {}
        for nombre, yf_sym, av_sym, td_sym, label, unit in metals:
            closes = _closes_yf(yf_sym)

            if closes is None and av_sym and av_key:
                closes = _closes_av_fx(av_sym, av_key)

            if closes is None and td_sym and td_key:
                closes = _closes_twelvedata(td_sym, td_key)

            if closes is None and yf_sym == "HG=F":
                closes = _closes_yf("COPX")
                if closes is None and td_key:
                    closes = _closes_twelvedata("HG/USD", td_key)

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
    import re
    import feedparser
    from config import get_settings

    s = get_settings()
    av_key      = s.alpha_vantage_key
    newsapi_key = s.newsapi_key

    def _fetch_av():
        if not av_key:
            return []
        try:
            r = requests.get(
                f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
                f"&tickers={ticker}&limit=15&apikey={av_key}",
                timeout=15,
            )
            data = r.json()
            if data.get("Information") or data.get("Note"):
                return []
            arts = []
            for art in data.get("feed", []):
                for ts in art.get("ticker_sentiment", []):
                    if ts.get("ticker") == ticker and float(ts.get("relevance_score", 0)) >= 0.05:
                        fd = art.get("time_published", "")[:8]
                        if len(fd) == 8:
                            fd = f"{fd[:4]}-{fd[4:6]}-{fd[6:8]}"
                        arts.append({
                            "titulo": art.get("title", ""),
                            "fecha": fd, "fuente": art.get("source", ""),
                            "score": float(art.get("overall_sentiment_score", 0)),
                            "label": art.get("overall_sentiment_label", "Neutral"),
                            "resumen": art.get("summary", "")[:220],
                            "url": art.get("url", ""),
                        })
                        break
            return arts
        except Exception:
            return []

    def _fetch_rss():
        try:
            q = requests.utils.quote(f"{ticker} Peru minera bolsa Lima")
            feed = feedparser.parse(
                f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=PE&ceid=PE:es-419"
            )
            arts = []
            for entry in (feed.entries or [])[:8]:
                resumen = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:220]
                arts.append({
                    "titulo": entry.get("title", ""),
                    "publicado": entry.get("published", ""),
                    "link": entry.get("link", ""),
                    "resumen": resumen,
                })
            return arts
        except Exception:
            return []

    def _fetch_newsapi():
        """Fallback NewsAPI cuando Alpha Vantage y RSS no retornan resultados."""
        if not newsapi_key:
            return []
        try:
            company_names = {
                "BVN": "Buenaventura", "SCCO": "Southern Copper",
                "CVERDEC1": "Cerro Verde", "MINSURI1": "Minsur",
                "VOLCABC1": "Volcan", "NEXAPEC1": "Nexa Resources",
                "BROCALC1": "El Brocal", "SHPC1": "Shougang",
                "PODERC1": "Poderosa", "MOROCOC1": "Morococha",
            }
            query = company_names.get(ticker, ticker) + " Peru mineria"
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": query, "language": "es", "sortBy": "publishedAt",
                        "pageSize": 8, "apiKey": newsapi_key},
                timeout=15,
            )
            data = r.json()
            arts = []
            for art in data.get("articles", []):
                arts.append({
                    "titulo":    art.get("title", ""),
                    "publicado": art.get("publishedAt", "")[:10],
                    "link":      art.get("url", ""),
                    "resumen":   (art.get("description") or "")[:220],
                    "fuente":    art.get("source", {}).get("name", "NewsAPI"),
                })
            return arts
        except Exception:
            return []

    av_arts, rss_arts = await asyncio.gather(
        asyncio.to_thread(_fetch_av),
        asyncio.to_thread(_fetch_rss),
    )

    # Activar NewsAPI solo si ambas fuentes principales fallaron
    newsapi_arts: list[dict] = []
    if not av_arts and not rss_arts and newsapi_key:
        newsapi_arts = await asyncio.to_thread(_fetch_newsapi)

    return {
        "ticker": ticker,
        "alpha_vantage": av_arts,
        "google_news": rss_arts if rss_arts else newsapi_arts,
    }

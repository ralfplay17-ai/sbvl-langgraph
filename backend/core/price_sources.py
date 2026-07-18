"""Fuentes compartidas de precios (commodities) y noticias con fallback en cascada.

Usado tanto por los endpoints REST (backend/api/market.py) como por las tools
LangChain de los agentes (backend/tools/commodities_tool.py, backend/tools/noticias_tool.py)
para no duplicar la lógica de fetch/fallback.
"""
import re
import requests
import yfinance as yf

# (nombre, yf_sym, av_fx_sym, td_etf_sym, label, unit)
# td_etf_sym: ETF accesible en plan gratuito de Twelve Data
METALS = [
    ("Oro",   "GC=F", "XAU", "GLD",  "XAU/USD", "oz"),
    ("Plata", "SI=F", "XAG", "SLV",  "XAG/USD", "oz"),
    ("Cobre", "HG=F", None,  "COPX", "HG=F",    "lb"),
]

COMPANY_NAMES_BVL = {
    "BVN": "Buenaventura", "SCCO": "Southern Copper",
    "CVERDEC1": "Cerro Verde", "MINSURI1": "Minsur",
    "VOLCABC1": "Volcan", "NEXAPEC1": "Nexa Resources",
    "BROCALC1": "El Brocal", "SHPC1": "Shougang",
    "PODERC1": "Poderosa", "MOROCOC1": "Morococha",
}


def closes_yf(symbol: str):
    """Serie de cierres de los últimos 20 días vía yfinance."""
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


def closes_av_fx(from_sym: str, av_key: str):
    """Fallback Alpha Vantage FX diario (ej. XAU, XAG)."""
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


def closes_twelvedata(symbol: str, td_key: str):
    """Fallback Twelve Data (ETF proxy para commodities)."""
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


def closes_con_fallback(yf_sym: str, av_sym: str | None, td_etf: str, av_key: str | None, td_key: str | None):
    """Cascada yfinance → Alpha Vantage FX → Twelve Data → ETF vía yfinance."""
    closes = closes_yf(yf_sym)

    if closes is None and av_sym and av_key:
        closes = closes_av_fx(av_sym, av_key)

    if closes is None and td_key:
        closes = closes_twelvedata(td_etf, td_key)

    if closes is None:
        closes = closes_yf(td_etf)  # ETF vía yfinance como último recurso

    return closes


def fetch_av_news(ticker: str, av_key: str) -> list[dict]:
    """Noticias con sentimiento vía Alpha Vantage NEWS_SENTIMENT."""
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


def fetch_google_news_rss(ticker: str) -> list[dict]:
    """Noticias vía Google News RSS en español."""
    try:
        import feedparser
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


def fetch_newsapi_news(ticker: str, newsapi_key: str) -> list[dict]:
    """Fallback NewsAPI cuando Alpha Vantage y RSS no retornan resultados."""
    if not newsapi_key:
        return []
    try:
        query = COMPANY_NAMES_BVL.get(ticker, ticker) + " Peru mineria"
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

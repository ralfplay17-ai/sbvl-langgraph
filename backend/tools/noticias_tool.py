import json
import re
import requests
from langchain_core.tools import tool


@tool
def obtener_noticias_bvl(ticker: str) -> str:
    """
    Obtiene noticias financieras recientes sobre una acción minera BVL.
    Fuentes: Alpha Vantage NEWS_SENTIMENT y Google News RSS en español.
    Input: ticker de la empresa (ej: BVN, SCCO).
    """
    from config import get_settings
    s = get_settings()
    av_key      = s.alpha_vantage_key
    newsapi_key = s.newsapi_key

    av_arts: list[dict] = []
    rss_arts: list[dict] = []

    # Alpha Vantage
    if av_key:
        try:
            r = requests.get(
                f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
                f"&tickers={ticker}&limit=15&apikey={av_key}",
                timeout=15,
            )
            data = r.json()
            if not data.get("Information") and not data.get("Note"):
                for art in data.get("feed", []):
                    for ts in art.get("ticker_sentiment", []):
                        if ts.get("ticker") == ticker and float(ts.get("relevance_score", 0)) >= 0.05:
                            fd = art.get("time_published", "")[:8]
                            if len(fd) == 8:
                                fd = f"{fd[:4]}-{fd[4:6]}-{fd[6:8]}"
                            av_arts.append({
                                "titulo":  art.get("title", ""),
                                "fecha":   fd,
                                "fuente":  art.get("source", ""),
                                "score":   float(art.get("overall_sentiment_score", 0)),
                                "label":   art.get("overall_sentiment_label", "Neutral"),
                                "resumen": art.get("summary", "")[:220],
                                "url":     art.get("url", ""),
                            })
                            break
        except Exception:
            pass

    # Google News RSS
    try:
        import feedparser
        q = requests.utils.quote(f"{ticker} Peru minera bolsa Lima")
        feed = feedparser.parse(
            f"https://news.google.com/rss/search?q={q}&hl=es-419&gl=PE&ceid=PE:es-419"
        )
        for entry in (feed.entries or [])[:8]:
            resumen = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:220]
            rss_arts.append({
                "titulo":    entry.get("title", ""),
                "publicado": entry.get("published", ""),
                "link":      entry.get("link", ""),
                "resumen":   resumen,
            })
    except Exception:
        pass

    # Fallback NewsAPI si ambas fuentes principales están vacías
    newsapi_arts: list[dict] = []
    if not av_arts and not rss_arts and newsapi_key:
        try:
            company_names = {
                "BVN": "Buenaventura", "SCCO": "Southern Copper",
                "CVERDEC1": "Cerro Verde", "MINSURI1": "Minsur",
                "VOLCABC1": "Volcan", "NEXAPEC1": "Nexa Resources",
            }
            query = company_names.get(ticker, ticker) + " Peru mineria"
            r = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": query, "language": "es", "sortBy": "publishedAt",
                        "pageSize": 8, "apiKey": newsapi_key},
                timeout=15,
            )
            for art in r.json().get("articles", []):
                newsapi_arts.append({
                    "titulo":    art.get("title", ""),
                    "publicado": art.get("publishedAt", "")[:10],
                    "link":      art.get("url", ""),
                    "resumen":   (art.get("description") or "")[:220],
                    "score":     0.0,
                    "label":     "Neutral",
                    "fuente":    art.get("source", {}).get("name", "NewsAPI"),
                })
        except Exception:
            pass

    todas_noticias = av_arts + (rss_arts if rss_arts else newsapi_arts)
    alcistas  = len([a for a in av_arts if a.get("score", 0) > 0.15])
    bajistas  = len([a for a in av_arts if a.get("score", 0) < -0.15])
    tendencia = "ALCISTA" if alcistas > bajistas else ("BAJISTA" if bajistas > alcistas else "NEUTRAL")

    return json.dumps({
        "ticker": ticker,
        "resumen_sentimiento": {
            "total_noticias": len(todas_noticias),
            "alcistas": alcistas,
            "bajistas": bajistas,
            "tendencia": tendencia,
        },
        "alpha_vantage": av_arts[:10],
        "google_news": (rss_arts if rss_arts else newsapi_arts)[:5],
    }, ensure_ascii=False)

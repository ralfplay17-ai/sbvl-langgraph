import json
from langchain_core.tools import tool
from core.price_sources import fetch_av_news, fetch_google_news_rss, fetch_newsapi_news


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

    av_arts  = fetch_av_news(ticker, av_key)
    rss_arts = fetch_google_news_rss(ticker)

    # Fallback NewsAPI si ambas fuentes principales están vacías
    newsapi_arts: list[dict] = []
    if not av_arts and not rss_arts and newsapi_key:
        newsapi_arts = fetch_newsapi_news(ticker, newsapi_key)

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

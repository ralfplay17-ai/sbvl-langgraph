import requests
import os
from langchain_core.tools import Tool


def build_noticias_bvl_tool(api_key: str = "") -> Tool:
    _api_key = api_key or os.environ.get("ALPHA_VANTAGE_KEY", "")

    def _fetch_news_ticker(ticker: str) -> list:
        for attempt in range(3):
            try:
                url = (
                    "https://www.alphavantage.co/query"
                    f"?function=NEWS_SENTIMENT&tickers={ticker}&limit=15&apikey={_api_key}"
                )
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                data = r.json()
                if data.get("Information") or data.get("Note"):
                    return []  # Rate limit diario — no reintentar
                feed = data.get("feed", [])
                relevant = []
                for art in feed:
                    for ts_item in art.get("ticker_sentiment", []):
                        if ts_item.get("ticker") == ticker:
                            rel = float(ts_item.get("relevance_score", 0))
                            if rel >= 0.05:
                                art2 = dict(art)
                                art2["_rel"] = rel
                                art2["_ts"] = float(ts_item.get("ticker_sentiment_score", 0))
                                relevant.append(art2)
                            break
                return relevant if relevant else feed
            except Exception:
                break
        return []

    def buscar_noticias(input_text: str = "") -> str:
        text_lower = input_text.lower()
        if "scco" in text_lower or "southern" in text_lower or "copper" in text_lower or "cobre" in text_lower:
            primary, secondary = "SCCO", "BVN"
        else:
            primary, secondary = "BVN", "SCCO"

        articles = _fetch_news_ticker(primary)
        if not articles:
            articles = _fetch_news_ticker(secondary)
            if articles:
                primary = secondary

        if not articles:
            return "No se encontraron noticias recientes para el sector minero peruano. Usa score=0 y confianza=0."

        alcistas = bajistas = neutros = 0
        lineas = []
        NL = "\n"

        for i, art in enumerate(articles[:8], 1):
            titulo = art.get("title", "Sin titulo")
            fecha = art.get("time_published", "")[:8]
            if len(fecha) == 8:
                fecha = fecha[:4] + "-" + fecha[4:6] + "-" + fecha[6:8]
            fuente = art.get("source", "Desconocida")
            label = art.get("overall_sentiment_label", "Neutral")
            score = float(art.get("overall_sentiment_score", 0))
            ts_score = art.get("_ts", score)
            resumen = art.get("summary", "")[:180]

            if score > 0.15:
                alcistas += 1
            elif score < -0.15:
                bajistas += 1
            else:
                neutros += 1

            lineas.append(
                f"[{i}] {titulo}" + NL +
                f"    Fecha: {fecha} | Fuente: {fuente}" + NL +
                f"    Sentimiento: {label} ({'+' if score >= 0 else ''}{score:.3f})"
                f" | Score ticker: {'+' if ts_score >= 0 else ''}{ts_score:.3f}" + NL +
                f"    {resumen}"
            )

        total = alcistas + bajistas + neutros
        tendencia = "ALCISTA" if alcistas > bajistas else ("BAJISTA" if bajistas > alcistas else "NEUTRAL")
        header = (
            f"TICKER: {primary} | {total} noticias analizadas" + NL +
            f"Alcistas: {alcistas} | Bajistas: {bajistas} | Neutras: {neutros}" + NL +
            f"Tendencia dominante: {tendencia}" + NL + NL
        )

        return header + (NL + NL).join(lineas)

    return Tool(
        name="buscar_noticias_bvl",
        description=(
            "Busca noticias financieras y sentimiento del mercado para acciones mineras BVL. "
            "Input: nombre de empresa o ticker (BVN, SCCO, Buenaventura, Southern Copper). "
            "SIEMPRE llama esta herramienta antes de dar tu analisis."
        ),
        func=buscar_noticias,
    )

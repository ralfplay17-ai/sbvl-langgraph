import requests
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.graph.workflow import ejecutar_analisis
from backend.db import guardar_analisis, obtener_historial_analisis, obtener_analisis_por_id, registrar_evento
import os

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    ticker: str
    include_news_prefetch: bool = True


def _prefetch_noticias(ticker: str) -> str:
    av_key = os.environ.get("ALPHA_VANTAGE_KEY", "")
    if not av_key:
        return ""

    primary = ticker.upper()
    secondary = "BVN" if primary == "SCCO" else "SCCO"

    def fetch_single(t: str) -> list:
        try:
            url = (
                f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
                f"&tickers={t}&limit=15&apikey={av_key}"
            )
            resp = requests.get(url, timeout=15).json()
            if resp.get("Information") or resp.get("Note"):
                return []
            feed = resp.get("feed", [])
            relevant = []
            for art in feed:
                for ts in art.get("ticker_sentiment", []):
                    if ts.get("ticker") == t and float(ts.get("relevance_score", 0)) >= 0.05:
                        art2 = dict(art)
                        art2["_ts"] = float(ts.get("ticker_sentiment_score", 0))
                        relevant.append(art2)
                        break
            return relevant if relevant else feed
        except Exception:
            return []

    articles = fetch_single(primary)
    if not articles:
        articles = fetch_single(secondary)
        if articles:
            primary = secondary

    if not articles:
        return ""

    alcistas = bajistas = neutros = 0
    lineas = []
    for i, art in enumerate(articles[:8], 1):
        titulo = art.get("title", "Sin titulo")
        fecha = art.get("time_published", "")[:8]
        if len(fecha) == 8:
            fecha = f"{fecha[:4]}-{fecha[4:6]}-{fecha[6:8]}"
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
            f"[{i}] {titulo}\n"
            f"    Fecha:{fecha} | Sentimiento:{label}({score:+.3f}) | Ticker:{ts_score:+.3f}\n"
            f"    {resumen}"
        )

    total = alcistas + bajistas + neutros
    tendencia = "ALCISTA" if alcistas > bajistas else ("BAJISTA" if bajistas > alcistas else "NEUTRAL")
    bloque = (
        f"[NOTICIAS_PREFETCH ticker={primary}]\n"
        f"Total:{total} | Alcistas:{alcistas} | Bajistas:{bajistas} | Neutras:{neutros}\n"
        f"Tendencia:{tendencia}\n\n" + "\n\n".join(lineas)
    )
    return bloque


@router.post("/run")
async def run_analysis(req: AnalysisRequest, background_tasks: BackgroundTasks):
    ticker = req.ticker.upper()
    if ticker not in ("BVN", "SCCO"):
        raise HTTPException(status_code=400, detail="Ticker debe ser BVN o SCCO")

    noticias = _prefetch_noticias(ticker) if req.include_news_prefetch else ""

    try:
        resultado = await ejecutar_analisis(ticker, noticias)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

    background_tasks.add_task(guardar_analisis, ticker, resultado)
    background_tasks.add_task(
        registrar_evento,
        "analisis_ejecutado",
        {"ticker": ticker, "senal": resultado.get("senal_final")},
    )

    return resultado


@router.get("/history")
async def get_history(ticker: str | None = None, limit: int = 20):
    return await obtener_historial_analisis(ticker, limit)


@router.get("/{analisis_id}")
async def get_analysis(analisis_id: str):
    result = await obtener_analisis_por_id(analisis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    return result

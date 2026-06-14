import logging
from config import get_settings

logger = logging.getLogger(__name__)


def _client():
    from supabase import create_client
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_key:
        logger.warning("[supabase] SUPABASE_URL o SUPABASE_SERVICE_KEY no configurados")
        return None
    return create_client(s.supabase_url, s.supabase_service_key)


async def guardar_analisis(resultado: dict) -> None:
    import asyncio
    client = _client()
    if not client:
        return
    try:
        senal = resultado.get("senal_final", "")
        if senal not in ("COMPRAR", "MANTENER", "VENDER"):
            senal = "MANTENER"
        row = {
            "ticker":          resultado.get("ticker", ""),
            "senal_final":     senal,
            "score_final":     float(resultado.get("score_final", 0)),
            "confianza_final": float(resultado.get("confianza_final", 0)),
            "pso_config":      resultado.get("pso_config", {}),
            "agentes_result":  resultado.get("detalle_agentes", {}),
            "pso_result": {
                "pesos":        resultado.get("pesos_utilizados", {}),
                "convergencia": resultado.get("historial_convergencia", []),
            },
        }
        await asyncio.to_thread(
            lambda: client.table("analysis_history").insert(row).execute()
        )
        logger.info("[supabase] Guardado: %s %s score=%.2f", row["ticker"], row["senal_final"], row["score_final"])
    except Exception as e:
        logger.error("[supabase] Error al guardar análisis: %s", e)


async def obtener_historial(ticker: str | None = None, limit: int = 20) -> list[dict]:
    import asyncio
    try:
        client = _client()
        if not client:
            return []

        def _query():
            q = client.table("analysis_history").select("*").order("created_at", desc=True).limit(limit)
            if ticker:
                q = q.eq("ticker", ticker)
            return q.execute()

        resp = await asyncio.to_thread(_query)
        data = resp.data or []
        logger.info("[supabase] Historial: %d registros devueltos (ticker=%s)", len(data), ticker)
        return data
    except Exception as e:
        logger.error("[supabase] Error al obtener historial: %s", e)
        return []


async def obtener_ultimo_analisis(ticker: str) -> dict | None:
    import asyncio
    try:
        client = _client()
        if not client:
            return None
        resp = await asyncio.to_thread(
            lambda: client.table("analysis_history")
                .select("*")
                .eq("ticker", ticker)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
        )
        data = resp.data or []
        return data[0] if data else None
    except Exception as e:
        logger.error("[supabase] Error al obtener último análisis: %s", e)
        return None

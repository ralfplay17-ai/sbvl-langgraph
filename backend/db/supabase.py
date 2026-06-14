from config import get_settings


def _client():
    from supabase import create_client
    s = get_settings()
    if not s.supabase_url or not s.supabase_service_key:
        return None
    return create_client(s.supabase_url, s.supabase_service_key)


async def guardar_analisis(resultado: dict) -> None:
    client = _client()
    if not client:
        return
    try:
        import asyncio
        row = {
            "ticker":          resultado.get("ticker", ""),
            "senal_final":     resultado.get("senal_final", ""),
            "score_final":     resultado.get("score_final", 0),
            "confianza_final": resultado.get("confianza_final", 0),
            "pso_config":      resultado.get("pso_config", {}),
            "agentes_result":  resultado.get("detalle_agentes", {}),
            "pso_result": {
                "pesos":       resultado.get("pesos_utilizados", {}),
                "convergencia": resultado.get("historial_convergencia", []),
            },
        }
        await asyncio.to_thread(
            lambda: client.table("analysis_history").insert(row).execute()
        )
    except Exception:
        pass


async def obtener_historial(ticker: str | None = None, limit: int = 20) -> list[dict]:
    client = _client()
    if not client:
        return []
    try:
        import asyncio
        def _query():
            q = client.table("analysis_history").select("*").order("created_at", desc=True).limit(limit)
            if ticker:
                q = q.eq("ticker", ticker)
            return q.execute()

        resp = await asyncio.to_thread(_query)
        return resp.data or []
    except Exception:
        return []


async def obtener_ultimo_analisis(ticker: str) -> dict | None:
    client = _client()
    if not client:
        return None
    try:
        import asyncio
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
    except Exception:
        return None

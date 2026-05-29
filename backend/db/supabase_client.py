import os
import json
from datetime import datetime

_client = None
_supabase_available = False


def _init_client():
    global _client, _supabase_available
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not key:
        return False
    try:
        from supabase import create_client
        _client = create_client(url, key)
        _supabase_available = True
        return True
    except Exception:
        return False


def get_client():
    global _client
    if _client is None:
        _init_client()
    return _client


def is_available() -> bool:
    if _client is not None:
        return True
    return _init_client()


# ── Análisis ────────────────────────────────────────────────────────────────

async def guardar_analisis(ticker: str, resultado: dict) -> dict:
    if not is_available():
        return {}
    client = get_client()
    record = {
        "ticker": ticker,
        "senal_final": resultado.get("senal_final", "MANTENER"),
        "score_final": resultado.get("score_final", 0),
        "confianza_final": resultado.get("confianza_final", 0),
        "pesos_pso": resultado.get("pesos_utilizados", {}),
        "senales_agentes": resultado.get("senales_agentes", {}),
        "scores_agentes": resultado.get("scores_agentes", {}),
        "confianzas_agentes": resultado.get("confianzas_agentes", {}),
        "factores_clave": resultado.get("factores_clave", []),
        "resultado_completo": resultado,
        "created_at": datetime.utcnow().isoformat(),
    }
    try:
        response = client.table("analisis").insert(record).execute()
        return response.data[0] if response.data else record
    except Exception:
        return {}


async def obtener_historial_analisis(ticker: str | None = None, limit: int = 20) -> list:
    if not is_available():
        return []
    client = get_client()
    try:
        query = (
            client.table("analisis")
            .select("id, ticker, senal_final, score_final, confianza_final, pesos_pso, senales_agentes, factores_clave, created_at")
            .order("created_at", desc=True)
            .limit(limit)
        )
        if ticker:
            query = query.eq("ticker", ticker)
        response = query.execute()
        return response.data or []
    except Exception:
        return []


async def obtener_analisis_por_id(analisis_id: str) -> dict | None:
    if not is_available():
        return None
    client = get_client()
    try:
        response = client.table("analisis").select("*").eq("id", analisis_id).single().execute()
        return response.data
    except Exception:
        return None


# ── Conversaciones ────────────────────────────────────────────────────────────

async def guardar_mensaje(session_id: str, role: str, content: str) -> dict:
    if not is_available():
        return {"session_id": session_id, "role": role, "content": content}
    client = get_client()
    record = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
    }
    try:
        response = client.table("conversaciones").insert(record).execute()
        return response.data[0] if response.data else record
    except Exception:
        return record


async def obtener_conversacion(session_id: str) -> list:
    if not is_available():
        return []
    client = get_client()
    try:
        response = (
            client.table("conversaciones")
            .select("role, content, created_at")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        return response.data or []
    except Exception:
        return []


# ── Audit log ────────────────────────────────────────────────────────────────

async def registrar_evento(evento: str, detalle: dict) -> None:
    if not is_available():
        return
    client = get_client()
    try:
        record = {
            "evento": evento,
            "detalle": detalle,
            "created_at": datetime.utcnow().isoformat(),
        }
        client.table("audit_log").insert(record).execute()
    except Exception:
        pass

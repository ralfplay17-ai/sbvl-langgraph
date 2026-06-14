import json
import re
from pydantic import BaseModel, Field, field_validator


class AgentOutput(BaseModel):
    agente: str
    ticker: str
    senal: str = "MANTENER"
    score: float = Field(default=0.0, ge=-1.0, le=1.0)
    confianza: float = Field(default=0.3, ge=0.0, le=1.0)
    datos_usados: str = ""
    justificacion: str = ""

    @field_validator("senal")
    @classmethod
    def validate_senal(cls, v):
        normalized = str(v).upper().strip()
        return normalized if normalized in {"COMPRAR", "VENDER", "MANTENER"} else "MANTENER"

    @field_validator("score", "confianza", mode="before")
    @classmethod
    def coerce_float(cls, v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0


def parse_agent_result(text: str, agente: str, ticker: str) -> dict:
    """
    Extrae y valida el JSON que el LLM devuelve como respuesta final.
    Maneja: markdown code-fences, JSON embebido en prosa, tipos incorrectos.
    Siempre devuelve un dict válido con todos los campos requeridos.
    """
    text = text.strip()

    # Extraer bloque de markdown si está presente
    for pattern in [r"```json\s*(\{.*?\})\s*```", r"```\s*(\{.*?\})\s*```"]:
        m = re.search(pattern, text, re.DOTALL)
        if m:
            text = m.group(1)
            break

    # Buscar el objeto JSON más externo
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            raw = json.loads(text[start:end + 1])
            raw.setdefault("agente", agente)
            raw.setdefault("ticker", ticker)
            return AgentOutput(**raw).model_dump()
        except Exception:
            pass

    return AgentOutput(
        agente=agente,
        ticker=ticker,
        senal="MANTENER",
        score=0.0,
        confianza=0.3,
        datos_usados="Error al parsear respuesta del LLM",
        justificacion=text[:200],
    ).model_dump()

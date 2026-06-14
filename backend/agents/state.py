from typing import TypedDict, Annotated
import operator
from pso.consensus import PSOConfig


class AgentResult(TypedDict):
    agente: str
    ticker: str
    senal: str
    score: float
    confianza: float
    datos_usados: str
    justificacion: str


class AnalysisState(TypedDict):
    ticker: str
    pso_config: PSOConfig
    tecnico: AgentResult | None
    commodities: AgentResult | None
    sentimiento: AgentResult | None
    riesgo: AgentResult | None
    pso_result: dict | None
    resultado_final: dict | None
    # Lista de eventos para SSE — se acumula con operator.add
    events: Annotated[list[dict], operator.add]

import asyncio
import json
import os
from typing import TypedDict

from langgraph.graph import StateGraph, END

from backend.agents.agente_tecnico import ejecutar_agente_tecnico
from backend.agents.agente_commodities import ejecutar_agente_commodities
from backend.agents.agente_sentimiento import ejecutar_agente_sentimiento
from backend.agents.agente_riesgo import ejecutar_agente_riesgo
from backend.agents.agente_coordinador import ejecutar_coordinador
from backend.pso.consensus_engine import run_pso


class GraphState(TypedDict):
    ticker: str
    input_message: str
    resultado_tecnico: str
    resultado_commodities: str
    resultado_sentimiento: str
    resultado_riesgo: str
    resultado_pso: dict
    resultado_final: dict
    error: str | None


async def nodo_agentes_paralelos(state: GraphState) -> dict:
    ticker = state["ticker"]
    input_msg = state["input_message"]

    av_key = os.environ.get("ALPHA_VANTAGE_KEY", "")
    td_key = os.environ.get("TWELVE_DATA_KEY", "")

    def _fallback(agente: str, err: Exception) -> str:
        return json.dumps({
            "agente": agente, "ticker": ticker,
            "senal": "MANTENER", "score": 0, "confianza": 0,
            "datos_usados": f"Error: {str(err)}",
            "justificacion": "Agente no disponible",
        })

    results = await asyncio.gather(
        ejecutar_agente_tecnico(ticker, av_key),
        ejecutar_agente_commodities(ticker, td_key, av_key),
        ejecutar_agente_sentimiento(input_msg, av_key),
        ejecutar_agente_riesgo(ticker),
        return_exceptions=True,
    )

    return {
        "resultado_tecnico": str(results[0]) if not isinstance(results[0], Exception) else _fallback("tecnico", results[0]),
        "resultado_commodities": str(results[1]) if not isinstance(results[1], Exception) else _fallback("commodities", results[1]),
        "resultado_sentimiento": str(results[2]) if not isinstance(results[2], Exception) else _fallback("sentimiento", results[2]),
        "resultado_riesgo": str(results[3]) if not isinstance(results[3], Exception) else _fallback("riesgo", results[3]),
    }


def nodo_pso(state: GraphState) -> dict:
    resultado_pso = run_pso(
        agente_tecnico=state["resultado_tecnico"],
        agente_commodities=state["resultado_commodities"],
        agente_sentimiento=state["resultado_sentimiento"],
        agente_riesgo=state["resultado_riesgo"],
    )
    return {"resultado_pso": resultado_pso}


async def nodo_coordinador(state: GraphState) -> dict:
    pso_str = json.dumps(state["resultado_pso"], ensure_ascii=False, indent=2)
    resultado_raw = await ejecutar_coordinador(pso_str)

    try:
        import re
        match = re.search(r"\{.*\}", resultado_raw, re.DOTALL)
        resultado_final = json.loads(match.group()) if match else json.loads(resultado_raw)
    except Exception:
        resultado_final = {"raw_output": resultado_raw, "pso": state["resultado_pso"]}

    return {"resultado_final": resultado_final}


def build_workflow():
    workflow = StateGraph(GraphState)
    workflow.add_node("agentes_paralelos", nodo_agentes_paralelos)
    workflow.add_node("pso", nodo_pso)
    workflow.add_node("coordinador", nodo_coordinador)
    workflow.set_entry_point("agentes_paralelos")
    workflow.add_edge("agentes_paralelos", "pso")
    workflow.add_edge("pso", "coordinador")
    workflow.add_edge("coordinador", END)
    return workflow.compile()


async def ejecutar_analisis(ticker: str, noticias_prefetch: str = "") -> dict:
    input_message = f"Analiza {ticker}"
    if noticias_prefetch:
        input_message += f"\n\n{noticias_prefetch}"

    graph = build_workflow()
    initial_state: GraphState = {
        "ticker": ticker,
        "input_message": input_message,
        "resultado_tecnico": "",
        "resultado_commodities": "",
        "resultado_sentimiento": "",
        "resultado_riesgo": "",
        "resultado_pso": {},
        "resultado_final": {},
        "error": None,
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state["resultado_final"]

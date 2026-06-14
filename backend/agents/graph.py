import asyncio
from langgraph.graph import StateGraph, START, END
from agents.state import AnalysisState
from agents.tecnico import run_tecnico
from agents.commodities import run_commodities
from agents.sentimiento import run_sentimiento
from agents.riesgo import run_riesgo
from pso.consensus import run_pso, PSOConfig
from config import get_llm


# ─── Nodos ────────────────────────────────────────────────────────────────────

async def agentes_paralelo(state: AnalysisState) -> dict:
    """Ejecuta los 4 agentes en paralelo y emite eventos por cada uno."""
    llm = get_llm()
    ticker = state["ticker"]

    # Ejecutar en paralelo con as_completed para emitir eventos conforme terminan
    results: dict[str, dict | None] = {"tecnico": None, "commodities": None, "sentimiento": None, "riesgo": None}
    events: list[dict] = []

    async def _run(name: str, coro):
        events.append({"type": "agent_start", "agent": name})
        try:
            result = await coro
        except Exception as e:
            result = {
                "agente": name, "ticker": ticker,
                "senal": "MANTENER", "score": 0.0, "confianza": 0.3,
                "datos_usados": f"Error: {str(e)[:100]}",
                "justificacion": "Fallo durante la ejecución del agente.",
            }
        results[name] = result
        events.append({"type": "agent_complete", "agent": name, "result": result})

    await asyncio.gather(
        _run("tecnico",     run_tecnico(ticker, llm)),
        _run("commodities", run_commodities(ticker, llm)),
        _run("sentimiento", run_sentimiento(ticker, llm)),
        _run("riesgo",      run_riesgo(ticker, llm)),
    )

    return {
        "tecnico":     results["tecnico"],
        "commodities": results["commodities"],
        "sentimiento": results["sentimiento"],
        "riesgo":      results["riesgo"],
        "events":      events,
    }


async def pso_consensus(state: AnalysisState) -> dict:
    """Ejecuta el PSO con los resultados de los 4 agentes."""
    agents_data = [
        state["tecnico"]     or {"agente": "tecnico",     "score": 0.0, "confianza": 0.3, "senal": "MANTENER"},
        state["commodities"] or {"agente": "commodities", "score": 0.0, "confianza": 0.3, "senal": "MANTENER"},
        state["sentimiento"] or {"agente": "sentimiento", "score": 0.0, "confianza": 0.3, "senal": "MANTENER"},
        state["riesgo"]      or {"agente": "riesgo",      "score": 0.0, "confianza": 0.3, "senal": "MANTENER"},
    ]

    config = state.get("pso_config") or PSOConfig()
    pso_result = await asyncio.to_thread(run_pso, agents_data, config)

    return {
        "pso_result": pso_result,
        "events": [{"type": "pso_complete", "result": pso_result}],
    }


async def coordinador(state: AnalysisState) -> dict:
    """Compone el resultado final consolidado para el dashboard."""
    pso = state["pso_result"] or {}
    ticker = state["ticker"]

    ag = {
        "tecnico":     state["tecnico"]     or {},
        "commodities": state["commodities"] or {},
        "sentimiento": state["sentimiento"] or {},
        "riesgo":      state["riesgo"]      or {},
    }

    senal = pso.get("senal_final", "MANTENER")
    score = pso.get("score_final", 0.0)
    conf  = pso.get("confianza_final", 0.0)

    nivel_conf = "alta" if conf >= 0.75 else ("media" if conf >= 0.55 else "baja")

    factores: list[str] = []
    for nombre, ag_data in ag.items():
        s = ag_data.get("justificacion", "")
        if s:
            factores.append(f"[{nombre.upper()}] {s[:120]}")

    resultado = {
        "ticker": ticker,
        "senal_final": senal,
        "score_final": score,
        "confianza_final": conf,
        "pesos_utilizados": pso.get("pesos_utilizados", {}),
        "historial_convergencia": pso.get("historial_convergencia", []),
        "pso_config": pso.get("config", {}),
        "detalle_agentes": {
            nombre: {
                "senal":       d.get("senal", "MANTENER"),
                "score":       d.get("score", 0.0),
                "confianza":   d.get("confianza", 0.0),
                "datos_usados": d.get("datos_usados", ""),
                "resumen":     d.get("justificacion", "")[:160],
            }
            for nombre, d in ag.items()
        },
        "factores_clave": factores,
        "dashboard": {
            "nivel_confianza": nivel_conf,
            "color_senal": "verde" if senal == "COMPRAR" else ("rojo" if senal == "VENDER" else "amarillo"),
            "resumen_corto": _resumen_corto(senal, ag, ticker),
        },
    }

    return {
        "resultado_final": resultado,
        "events": [{"type": "final", "result": resultado}],
    }


def _resumen_corto(senal: str, ag: dict, ticker: str) -> str:
    partes = []
    if ag.get("sentimiento", {}).get("score", 0) > 0.5:
        partes.append("sentimiento alcista fuerte")
    if ag.get("commodities", {}).get("score", 0) > 0.3:
        partes.append("commodities positivos")
    if ag.get("tecnico", {}).get("score", 0) > 0.3:
        partes.append("señal técnica favorable")
    if ag.get("riesgo", {}).get("score", 0) > 0.3:
        partes.append("riesgo macroeconómico favorable")

    if not partes:
        return f"Señal {senal} para {ticker} con confianza media."
    return f"Señal de {senal} con {', '.join(partes[:2])}."


# ─── Grafo ────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(AnalysisState)
    g.add_node("agentes",      agentes_paralelo)
    g.add_node("pso",          pso_consensus)
    g.add_node("coordinador",  coordinador)

    g.add_edge(START,          "agentes")
    g.add_edge("agentes",      "pso")
    g.add_edge("pso",          "coordinador")
    g.add_edge("coordinador",  END)

    return g.compile()


graph = build_graph()

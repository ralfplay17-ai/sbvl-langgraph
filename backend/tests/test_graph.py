import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import agents.graph as graph_module
from pso.consensus import PSOConfig


def _agent_result(nombre, ticker, senal, score, confianza):
    return {
        "agente": nombre, "ticker": ticker, "senal": senal,
        "score": score, "confianza": confianza,
        "datos_usados": f"datos de prueba para {nombre}",
        "justificacion": f"justificación de prueba para {nombre}",
    }


def _estado_inicial(ticker="BVN"):
    return {
        "ticker": ticker,
        "pso_config": PSOConfig(n_particles=10, iters=15),
        "tecnico": None, "commodities": None, "sentimiento": None, "riesgo": None,
        "pso_result": None, "resultado_final": None,
        "events": [],
    }


def test_grafo_camino_feliz(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: None)

    async def ok_tecnico(ticker, llm):
        return _agent_result("tecnico", ticker, "COMPRAR", 0.6, 0.8)

    async def ok_commodities(ticker, llm):
        return _agent_result("commodities", ticker, "COMPRAR", 0.4, 0.7)

    async def ok_sentimiento(ticker, llm):
        return _agent_result("sentimiento", ticker, "MANTENER", 0.0, 0.5)

    async def ok_riesgo(ticker, llm):
        return _agent_result("riesgo", ticker, "COMPRAR", 0.3, 0.6)

    monkeypatch.setattr(graph_module, "run_tecnico", ok_tecnico)
    monkeypatch.setattr(graph_module, "run_commodities", ok_commodities)
    monkeypatch.setattr(graph_module, "run_sentimiento", ok_sentimiento)
    monkeypatch.setattr(graph_module, "run_riesgo", ok_riesgo)

    resultado = asyncio.run(graph_module.graph.ainvoke(_estado_inicial()))

    final = resultado["resultado_final"]
    assert final["ticker"] == "BVN"
    assert final["senal_final"] in ("COMPRAR", "VENDER", "MANTENER")
    assert final["error_sistema"] is None
    assert set(final["detalle_agentes"].keys()) == {"tecnico", "commodities", "sentimiento", "riesgo"}
    assert abs(sum(final["pesos_utilizados"].values()) - 1.0) < 1e-3

    tipos_eventos = [e["type"] for e in resultado["events"]]
    assert tipos_eventos.count("agent_start") == 4
    assert tipos_eventos.count("agent_complete") == 4
    assert "pso_complete" in tipos_eventos
    assert tipos_eventos[-1] == "final"


def test_grafo_degrada_cuando_un_agente_falla(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: None)

    async def falla_tecnico(ticker, llm):
        raise RuntimeError("timeout simulado del LLM")

    async def ok_commodities(ticker, llm):
        return _agent_result("commodities", ticker, "MANTENER", 0.0, 0.5)

    async def ok_sentimiento(ticker, llm):
        return _agent_result("sentimiento", ticker, "MANTENER", 0.0, 0.5)

    async def ok_riesgo(ticker, llm):
        return _agent_result("riesgo", ticker, "MANTENER", 0.0, 0.5)

    monkeypatch.setattr(graph_module, "run_tecnico", falla_tecnico)
    monkeypatch.setattr(graph_module, "run_commodities", ok_commodities)
    monkeypatch.setattr(graph_module, "run_sentimiento", ok_sentimiento)
    monkeypatch.setattr(graph_module, "run_riesgo", ok_riesgo)

    resultado = asyncio.run(graph_module.graph.ainvoke(_estado_inicial()))

    final = resultado["resultado_final"]
    assert final["error_sistema"] is not None
    assert "timeout simulado del LLM" in final["error_sistema"]
    assert final["detalle_agentes"]["tecnico"]["senal"] == "MANTENER"
    assert final["detalle_agentes"]["tecnico"]["score"] == 0.0
    # El pipeline completo debe seguir produciendo un resultado, no debe propagar la excepción
    assert final["senal_final"] in ("COMPRAR", "VENDER", "MANTENER")

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

import agents.graph as graph_module
import api.analyze as analyze_module
import api.history as history_module
from main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "2.0.0"}


def test_market_tickers_es_estatico_y_no_esta_vacio():
    resp = client.get("/api/market/tickers")
    assert resp.status_code == 200
    tickers = resp.json()["tickers"]
    assert len(tickers) >= 10
    assert any(t["value"] == "BVN" for t in tickers)


def test_history_devuelve_lo_que_retorna_la_capa_de_datos(monkeypatch):
    async def fake_obtener_historial(ticker=None, limit=20):
        return [{"ticker": "BVN", "senal_final": "COMPRAR", "score_final": 0.5}]

    monkeypatch.setattr(history_module, "obtener_historial", fake_obtener_historial)

    resp = client.get("/api/history?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "BVN"


def test_history_last_devuelve_none_si_no_hay_registros(monkeypatch):
    async def fake_obtener_ultimo(ticker):
        return None

    monkeypatch.setattr(history_module, "obtener_ultimo_analisis", fake_obtener_ultimo)

    resp = client.get("/api/history/BVN/last")
    assert resp.status_code == 200
    assert resp.json() is None


def _agent_result(nombre, ticker, senal, score, confianza):
    return {
        "agente": nombre, "ticker": ticker, "senal": senal,
        "score": score, "confianza": confianza,
        "datos_usados": f"datos de prueba para {nombre}",
        "justificacion": f"justificación de prueba para {nombre}",
    }


def test_analyze_sse_stream_completo(monkeypatch):
    monkeypatch.setattr(graph_module, "get_llm", lambda: None)
    monkeypatch.setattr(graph_module, "run_tecnico", _make_agent("tecnico", "COMPRAR", 0.5, 0.7))
    monkeypatch.setattr(graph_module, "run_commodities", _make_agent("commodities", "MANTENER", 0.0, 0.5))
    monkeypatch.setattr(graph_module, "run_sentimiento", _make_agent("sentimiento", "COMPRAR", 0.4, 0.6))
    monkeypatch.setattr(graph_module, "run_riesgo", _make_agent("riesgo", "MANTENER", 0.1, 0.5))

    guardados = []

    async def fake_guardar(resultado):
        guardados.append(resultado)

    monkeypatch.setattr(analyze_module, "guardar_analisis", fake_guardar)

    payload = {
        "ticker": "BVN",
        "pso_config": {"n_particles": 10, "iters": 50, "c1": 0.5, "c2": 0.3, "w": 0.9},
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200

    eventos = [
        json.loads(line[len("data: "):])
        for line in resp.text.splitlines()
        if line.startswith("data: ")
    ]
    tipos = [e["type"] for e in eventos]

    assert tipos[0] == "start"
    assert tipos.count("agent_complete") == 4
    assert "pso_complete" in tipos
    assert "final" in tipos
    assert tipos[-1] == "close"

    final_event = next(e for e in eventos if e["type"] == "final")
    assert final_event["result"]["ticker"] == "BVN"
    assert "tiempo_ejecucion_s" in final_event["result"]

    # guardar_analisis se dispara de forma no bloqueante tras el evento final
    assert len(guardados) == 1
    assert guardados[0]["ticker"] == "BVN"


def _make_agent(nombre, senal, score, confianza):
    async def _run(ticker, llm):
        return _agent_result(nombre, ticker, senal, score, confianza)
    return _run

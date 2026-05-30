import numpy as np
import pyswarms as ps
import json
import re


def _normalizar_texto(entrada) -> str:
    if entrada is None:
        return ""
    if isinstance(entrada, dict):
        return json.dumps(entrada, ensure_ascii=False)
    if isinstance(entrada, str):
        return entrada
    return str(entrada)


def _extraer_json(entrada) -> dict:
    texto = _normalizar_texto(entrada).strip()
    if not texto:
        return {}

    try:
        return json.loads(texto)
    except Exception:
        pass

    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            return {}

    return {}


def _senal_a_valor(senal: str) -> float:
    senal = str(senal).upper().strip()
    if senal == "COMPRAR":
        return 1.0
    elif senal == "VENDER":
        return -1.0
    return 0.0


def _procesar_agente(entrada, nombre_agente: str) -> dict:
    data = _extraer_json(entrada)
    texto = _normalizar_texto(entrada)

    agente = data.get("agente", nombre_agente)
    ticker = data.get("ticker", "")
    senal = data.get("senal", data.get("señal", "MANTENER"))

    try:
        score = float(data.get("score"))
    except Exception:
        score = _senal_a_valor(senal)

    score = max(-1.0, min(1.0, score))

    try:
        confianza = float(data.get("confianza", 0.5))
    except Exception:
        confianza = 0.5

    if confianza > 1:
        confianza = confianza / 100.0

    confianza = max(0.0, min(1.0, confianza))

    datos_usados = data.get("datos_usados", "")
    justificacion = data.get("justificacion", data.get("razon", ""))

    if not data:
        texto_upper = texto.upper()
        if "COMPRAR" in texto_upper:
            senal, score = "COMPRAR", 1.0
        elif "VENDER" in texto_upper:
            senal, score = "VENDER", -1.0
        else:
            senal, score = "MANTENER", 0.0
        confianza = 0.5
        datos_usados = "No se pudo extraer JSON estructurado"
        justificacion = "Se aplicó lectura de respaldo desde texto."

    return {
        "agente": agente,
        "ticker": ticker,
        "senal": senal,
        "score": score,
        "confianza": confianza,
        "datos_usados": datos_usados,
        "justificacion": justificacion,
    }


def run_pso(
    agente_tecnico: str,
    agente_commodities: str,
    agente_sentimiento: str,
    agente_riesgo: str,
) -> dict:
    agentes = [
        _procesar_agente(agente_tecnico, "tecnico"),
        _procesar_agente(agente_commodities, "commodities"),
        _procesar_agente(agente_sentimiento, "sentimiento"),
        _procesar_agente(agente_riesgo, "riesgo"),
    ]

    scores = np.array([a["score"] for a in agentes], dtype=float)
    confianzas = np.array([a["confianza"] for a in agentes], dtype=float)

    if confianzas.sum() == 0:
        confianzas = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
    else:
        confianzas = confianzas / confianzas.sum()

    def objective_function(particles):
        costs = []
        for particle in particles:
            pesos = np.abs(particle)
            if pesos.sum() == 0:
                pesos = np.array([0.25, 0.25, 0.25, 0.25])
            else:
                pesos = pesos / pesos.sum()

            score_pso = np.dot(pesos, scores)

            confianza_penalty = np.sum((pesos - confianzas) ** 2)

            entropia = -np.sum(pesos * np.log(pesos + 1e-10))
            desbalance_penalty = -entropia

            senales_activas = np.abs(scores) > 0.1
            if senales_activas.sum() > 1:
                hay_positivas = (scores[senales_activas] > 0).sum() > 0
                hay_negativas = (scores[senales_activas] < 0).sum() > 0
                if hay_positivas and hay_negativas and abs(score_pso) > 0.7:
                    coherencia_penalty = abs(score_pso) * 2
                else:
                    coherencia_penalty = 0
            else:
                coherencia_penalty = 0

            cost = (
                confianza_penalty * 0.4 +
                desbalance_penalty * 0.3 +
                coherencia_penalty * 0.3
            )
            costs.append(cost)

        return np.array(costs)

    options = {"c1": 0.5, "c2": 0.3, "w": 0.9}
    bounds = (np.zeros(4), np.ones(4))

    optimizer = ps.single.GlobalBestPSO(
        n_particles=20,
        dimensions=4,
        options=options,
        bounds=bounds,
    )

    cost, best_pos = optimizer.optimize(objective_function, iters=50, verbose=False)

    pesos_optimos = np.abs(best_pos)
    if pesos_optimos.sum() == 0:
        pesos_optimos = np.array([0.25, 0.25, 0.25, 0.25])
    else:
        pesos_optimos = pesos_optimos / pesos_optimos.sum()

    score_final = float(np.dot(pesos_optimos, scores))

    if score_final >= 0.25:
        decision = "COMPRAR"
    elif score_final <= -0.25:
        decision = "VENDER"
    else:
        decision = "MANTENER"

    confianza_final = float(np.dot(pesos_optimos, np.array([a["confianza"] for a in agentes])))
    confianza_final = max(0.0, min(1.0, confianza_final))

    tickers = [a["ticker"] for a in agentes if a["ticker"]]
    ticker_final = tickers[0] if tickers else "DESCONOCIDO"

    return {
        "motor": "PSO Consensus Engine",
        "algoritmo": "PySwarms GlobalBestPSO",
        "configuracion": {
            "particulas": 20,
            "iteraciones": 50,
            "dimensiones": 4,
        },
        "ticker": ticker_final,
        "senal_final": decision,
        "score_final": round(score_final, 4),
        "confianza_final": round(confianza_final, 4),
        "pesos_optimos": {
            "tecnico": round(float(pesos_optimos[0]), 4),
            "commodities": round(float(pesos_optimos[1]), 4),
            "sentimiento": round(float(pesos_optimos[2]), 4),
            "riesgo": round(float(pesos_optimos[3]), 4),
        },
        "agentes": {
            "tecnico": agentes[0],
            "commodities": agentes[1],
            "sentimiento": agentes[2],
            "riesgo": agentes[3],
        },
        "costo_optimizacion": round(float(cost), 6),
    }

from dataclasses import dataclass
import numpy as np


@dataclass
class PSOConfig:
    n_particles: int = 50
    iters: int = 100
    c1: float = 0.5
    c2: float = 0.3
    w: float = 0.9


def run_pso(agents: list[dict], config: PSOConfig) -> dict:
    """
    Optimiza pesos de los 4 agentes usando PySwarms GlobalBestPSO.
    agents: lista de dicts con keys: agente, senal, score, confianza
    """
    import pyswarms as ps

    scores     = np.array([a.get("score", 0.0) for a in agents], dtype=float)
    confianzas = np.array([a.get("confianza", 0.25) for a in agents], dtype=float)

    # Normalizar confianzas como referencia para los pesos
    conf_norm = confianzas / confianzas.sum() if confianzas.sum() > 0 else np.full(4, 0.25)

    def objective(particles):
        costs = []
        for particle in particles:
            pesos = np.abs(particle)
            pesos = pesos / pesos.sum() if pesos.sum() > 0 else np.full(4, 0.25)

            score_pso = float(np.dot(pesos, scores))

            # Penalizar alejamiento de confianzas
            confianza_penalty = float(np.sum((pesos - conf_norm) ** 2))

            # Favorecer distribución balanceada (entropía)
            entropia = -float(np.sum(pesos * np.log(pesos + 1e-10)))
            desbalance_penalty = -entropia

            # Penalizar decisiones extremas con señales contrapuestas
            activas = np.abs(scores) > 0.1
            hay_positivas = (scores[activas] > 0).any() if activas.any() else False
            hay_negativas = (scores[activas] < 0).any() if activas.any() else False
            coherencia_penalty = abs(score_pso) * 2 if (hay_positivas and hay_negativas and abs(score_pso) > 0.7) else 0

            costs.append(confianza_penalty * 0.4 + desbalance_penalty * 0.3 + coherencia_penalty * 0.3)
        return np.array(costs)

    optimizer = ps.single.GlobalBestPSO(
        n_particles=config.n_particles,
        dimensions=4,
        options={"c1": config.c1, "c2": config.c2, "w": config.w},
        bounds=(np.zeros(4), np.ones(4)),
    )
    cost, best_pos = optimizer.optimize(objective, iters=config.iters, verbose=False)
    historial = [round(float(c), 6) for c in optimizer.cost_history]

    pesos = np.abs(best_pos)
    pesos = pesos / pesos.sum() if pesos.sum() > 0 else np.full(4, 0.25)

    score_final = float(np.dot(pesos, scores))
    confianza_final = float(np.dot(pesos, confianzas))
    confianza_final = max(0.0, min(1.0, confianza_final))

    if score_final >= 0.25:
        decision = "COMPRAR"
    elif score_final <= -0.25:
        decision = "VENDER"
    else:
        decision = "MANTENER"

    nombres = ["tecnico", "commodities", "sentimiento", "riesgo"]

    return {
        "senal_final": decision,
        "score_final": round(score_final, 4),
        "confianza_final": round(confianza_final, 4),
        "pesos_utilizados": {nombres[i]: round(float(pesos[i]), 4) for i in range(4)},
        "costo_optimizacion": round(float(cost), 6),
        "historial_convergencia": historial,
        "config": {
            "n_particles": config.n_particles,
            "iters": config.iters,
            "c1": config.c1,
            "c2": config.c2,
            "w": config.w,
        },
    }

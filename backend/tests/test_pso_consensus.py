import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pso.consensus import run_pso, PSOConfig

FAST_CONFIG = PSOConfig(n_particles=15, iters=30, c1=0.5, c2=0.3, w=0.9)


def _agentes(scores, confianzas=(0.8, 0.8, 0.8, 0.8)):
    nombres = ["tecnico", "commodities", "sentimiento", "riesgo"]
    return [
        {"agente": n, "senal": "MANTENER", "score": s, "confianza": c}
        for n, s, c in zip(nombres, scores, confianzas)
    ]


def test_pesos_suman_uno():
    result = run_pso(_agentes([0.6, 0.2, -0.1, 0.3]), FAST_CONFIG)
    total = sum(result["pesos_utilizados"].values())
    # Los pesos individuales vienen redondeados a 4 decimales, así que el
    # margen debe cubrir el error de redondeo acumulado, no solo el de float.
    assert abs(total - 1.0) < 1e-3


def test_senal_comprar_cuando_scores_fuertemente_positivos():
    result = run_pso(_agentes([0.9, 0.85, 0.8, 0.9]), FAST_CONFIG)
    assert result["senal_final"] == "COMPRAR"
    assert result["score_final"] > 0.25


def test_senal_vender_cuando_scores_fuertemente_negativos():
    result = run_pso(_agentes([-0.9, -0.85, -0.8, -0.9]), FAST_CONFIG)
    assert result["senal_final"] == "VENDER"
    assert result["score_final"] < -0.25


def test_senal_mantener_cuando_scores_neutros():
    result = run_pso(_agentes([0.0, 0.0, 0.0, 0.0]), FAST_CONFIG)
    assert result["senal_final"] == "MANTENER"


def test_confianza_final_dentro_de_rango():
    result = run_pso(_agentes([0.5, -0.3, 0.2, 0.1], confianzas=(0.9, 0.4, 0.6, 0.7)), FAST_CONFIG)
    assert 0.0 <= result["confianza_final"] <= 1.0


def test_config_usada_se_refleja_en_el_resultado():
    config = PSOConfig(n_particles=12, iters=20, c1=0.7, c2=0.4, w=0.8)
    result = run_pso(_agentes([0.3, 0.1, -0.2, 0.0]), config)
    assert result["config"] == {
        "n_particles": 12, "iters": 20, "c1": 0.7, "c2": 0.4, "w": 0.8,
    }


def test_historial_convergencia_tiene_un_valor_por_iteracion():
    result = run_pso(_agentes([0.4, -0.1, 0.2, 0.0]), FAST_CONFIG)
    assert len(result["historial_convergencia"]) == FAST_CONFIG.iters

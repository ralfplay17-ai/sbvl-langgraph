"""
Caso de Prueba 1.3 - "Validación de rango de configuración PSO (API)"

No es un test Selenium: el slider del dashboard (frontend/components/dashboard/PSOConfig.tsx)
ya limita n_particles a [10,200] e iters a [50,500], por lo que un valor fuera
de rango solo es alcanzable llamando directamente a la API (tal como describe
la propia plantilla de casos de prueba: "vía API directa /docs").
"""
import os

import requests

API_URL = os.environ.get("E2E_API_URL", "http://localhost:8000")


def test_caso_1_3_n_particles_por_encima_del_maximo_es_rechazado():
    resp = requests.post(
        f"{API_URL}/api/analyze",
        json={"ticker": "BVN", "pso_config": {"n_particles": 500, "iters": 100, "c1": 0.5, "c2": 0.3, "w": 0.9}},
        timeout=10,
    )
    assert resp.status_code == 422, f"Se esperaba 422, se obtuvo {resp.status_code}: {resp.text}"
    detail = resp.json()["detail"]
    assert any(d["loc"][-1] == "n_particles" for d in detail)
    print(f"[OK] n_particles=500 (máx 200) rechazado con 422: {detail}")


def test_caso_1_3_iters_por_debajo_del_minimo_es_rechazado():
    resp = requests.post(
        f"{API_URL}/api/analyze",
        json={"ticker": "BVN", "pso_config": {"n_particles": 50, "iters": 10, "c1": 0.5, "c2": 0.3, "w": 0.9}},
        timeout=10,
    )
    assert resp.status_code == 422, f"Se esperaba 422, se obtuvo {resp.status_code}: {resp.text}"
    detail = resp.json()["detail"]
    assert any(d["loc"][-1] == "iters" for d in detail)
    print(f"[OK] iters=10 (mín 50) rechazado con 422: {detail}")


def test_caso_1_3_configuracion_dentro_de_rango_es_aceptada():
    resp = requests.post(
        f"{API_URL}/api/analyze",
        json={"ticker": "BVN", "pso_config": {"n_particles": 50, "iters": 100, "c1": 0.5, "c2": 0.3, "w": 0.9}},
        timeout=15,
        stream=True,
    )
    assert resp.status_code == 200, f"Config válida debería aceptarse (200), se obtuvo {resp.status_code}"
    resp.close()
    print("[OK] Configuración PSO dentro de rango es aceptada (200, no 422)")

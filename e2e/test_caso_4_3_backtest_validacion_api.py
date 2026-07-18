"""
Caso de Prueba 4.3 - "Validación de rango de días vía API"

No es un test Selenium: la UI solo ofrece 4 botones de período fijos
(90/180/365/1825 días), por lo que el borde de validación de Pydantic
(30 <= dias <= 1825) solo es alcanzable llamando directamente a la API.
"""
import os

import requests

API_URL = os.environ.get("E2E_API_URL", "http://localhost:8000")


def test_caso_4_3_dias_por_debajo_del_minimo_es_rechazado():
    resp = requests.post(f"{API_URL}/api/backtest", json={"ticker": "BVN", "dias": 10}, timeout=10)
    assert resp.status_code == 422, f"Se esperaba 422, se obtuvo {resp.status_code}: {resp.text}"
    detail = resp.json()["detail"]
    assert any(d["loc"][-1] == "dias" for d in detail)
    print(f"[OK] dias=10 (mín 30) rechazado con 422: {detail}")


def test_caso_4_3_dias_por_encima_del_maximo_es_rechazado():
    resp = requests.post(f"{API_URL}/api/backtest", json={"ticker": "BVN", "dias": 5000}, timeout=10)
    assert resp.status_code == 422, f"Se esperaba 422, se obtuvo {resp.status_code}: {resp.text}"
    detail = resp.json()["detail"]
    assert any(d["loc"][-1] == "dias" for d in detail)
    print(f"[OK] dias=5000 (máx 1825) rechazado con 422: {detail}")


def test_caso_4_3_dias_dentro_de_rango_es_aceptado():
    resp = requests.post(f"{API_URL}/api/backtest", json={"ticker": "BVN", "dias": 90}, timeout=30)
    assert resp.status_code == 200, f"dias=90 debería aceptarse (200), se obtuvo {resp.status_code}"
    print("[OK] dias=90 es aceptado (200, no 422); el cuerpo puede traer error de datos, no de validación")

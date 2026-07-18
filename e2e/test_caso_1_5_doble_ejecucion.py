"""
Caso de Prueba 1.5 - "Prevención de doble ejecución concurrente"

Dispara dos clics consecutivos y verifica, a nivel de red (Chrome DevTools
Protocol), que solo se envía UNA petición POST /api/analyze -- es decir que
el guard `if (loading) return;` de handleAnalyze (page.tsx) realmente evita
la doble ejecución, en vez de confiar solo en observar el atributo
`disabled` del botón (que en este entorno puede resolverse demasiado rápido
para capturarlo de forma confiable, ver nota en conftest/caso 1.1).
"""
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import (
    abrir_dashboard,
    cerrar_modal_error_si_existe,
    esperar_analisis_terminado,
    seleccionar_ticker,
)


def contar_requests_analyze(driver, http_method: str = "POST") -> int:
    """Cuenta peticiones de red a /api/analyze filtrando por método HTTP.

    El navegador emite un preflight CORS `OPTIONS /api/analyze` además del
    `POST /api/analyze` real (la app cruza orígenes: frontend :3000 -> backend
    :8000 con Content-Type: application/json). Ambos matchean la URL, así que
    contar sin filtrar por método siempre da 2 aunque solo haya UN análisis
    disparado -- hay que filtrar explícitamente por request.method == "POST".
    """
    total = 0
    for entry in driver.get_log("performance"):
        try:
            msg = json.loads(entry["message"])["message"]
        except (KeyError, ValueError):
            continue
        if msg.get("method") != "Network.requestWillBeSent":
            continue
        request = msg.get("params", {}).get("request", {})
        if "/api/analyze" in request.get("url", "") and request.get("method") == http_method:
            total += 1
    return total


def test_caso_1_5_prevencion_doble_ejecucion_concurrente(driver, wait):
    abrir_dashboard(driver, wait)
    seleccionar_ticker(driver, wait, "BVN")

    boton = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//aside//button[contains(., 'Ejecutar Análisis')]")
    ))

    # Paso 1: clic inicial
    boton.click()

    # Paso 2: intentar un segundo clic de inmediato, sobre la MISMA referencia de
    # elemento. Si el botón ya está disabled, WebDriver puede rechazar el clic
    # (ElementNotInteractableException) -- lo cual también es una señal correcta
    # de que la protección funcionó -- o el clic puede no producir efecto porque
    # el atributo disabled bloquea el evento nativo del navegador.
    try:
        boton.click()
    except Exception as e:
        print(f"[OK] El segundo clic fue rechazado por el navegador: {type(e).__name__}")

    esperar_analisis_terminado(driver)
    cerrar_modal_error_si_existe(driver, wait)

    n_requests = contar_requests_analyze(driver, "POST")
    print(f"[INFO] Peticiones POST /api/analyze observadas: {n_requests}")
    assert n_requests == 1, (
        f"Se esperaba exactamente 1 petición a /api/analyze tras el doble clic, "
        f"se observaron {n_requests} (posible fuga del guard 'if (loading) return')."
    )
    print("[OK] Solo se disparó una petición de análisis pese al doble clic")

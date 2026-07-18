"""
Caso extra (complementa 4.1) - "Backtest falla gracefully sin fuente de datos"

El caso 4.1 (camino feliz de backtest) no es reproducible en este entorno
porque ejecutar_backtest() (backend/core/backtest.py) depende de yfinance,
que no tiene salida de red aquí. Lo que SÍ es determinista y vale la pena
probar es que el fallo se propaga correctamente hasta la UI como un mensaje
de error legible, en vez de dejar la pantalla colgada o mostrar un stack
trace.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import abrir_dashboard, ir_a_pestana


def test_extra_backtest_falla_gracefully_sin_datos(driver, wait):
    abrir_dashboard(driver, wait)
    ir_a_pestana(driver, wait, "Backtesting")

    boton = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(., 'Ejecutar Backtest')]")
    ))
    boton.click()

    wait.until(EC.text_to_be_present_in_element(
        (By.XPATH, "//button[contains(., 'Ejecutar Backtest') or contains(., 'Ejecutando')]"), "Ejecutar Backtest"
    ))

    error_banner = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[contains(@class,'text-red-300')]")
    ))
    assert "Sin datos" in error_banner.text
    print(f"[OK] El backtest sin datos de mercado muestra el error real en la UI: {error_banner.text!r}")

    # No debe haberse renderizado ninguna métrica (serían datos inventados)
    assert not driver.find_elements(By.XPATH, "//*[contains(text(),'Estrategia PSO')]")
    print("[OK] No se muestran métricas cuando el backtest falla (no se inventan datos)")

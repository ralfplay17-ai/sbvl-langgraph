"""
Caso de Prueba 5.5 - "Estado vacío sin ejecuciones registradas"

Sin SUPABASE_URL/SUPABASE_SERVICE_KEY configuradas en este entorno,
obtener_historial() devuelve una lista vacía de forma real (no simulada).
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import abrir_dashboard, ir_a_pestana


def test_caso_5_5_estado_vacio_sin_ejecuciones(driver, wait):
    abrir_dashboard(driver, wait)
    ir_a_pestana(driver, wait, "Historial")

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(),'Sin ejecuciones registradas todavía.')]")
    ))
    assert "Sin ejecuciones registradas todavía." in driver.page_source
    print("[OK] Mensaje de estado vacío presente")

    assert "Ejecutá un análisis desde el sidebar" in driver.page_source
    print("[OK] Texto guía 'Ejecutá un análisis desde el sidebar...' presente")

    # No debe mostrarse tabla ni filtros de ticker en el estado vacío
    filas_tabla = driver.find_elements(By.XPATH, "//div[contains(@class,'grid-cols-[140px_70px_110px_110px_55px_auto_28px]')]")
    assert len(filas_tabla) == 0, "No debería haber filas de tabla con el historial vacío"
    print("[OK] No se renderiza la tabla de historial cuando no hay registros")

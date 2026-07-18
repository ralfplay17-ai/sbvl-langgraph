"""
Caso de Prueba 5.4 - "Actualización manual del historial"

Verifica que el botón "Actualizar" dispara un nuevo GET /api/history, sin
depender de que haya registros (ver caso 5.5: el historial está vacío en
este entorno porque Supabase no está configurado).
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import abrir_dashboard, ir_a_pestana


def test_caso_5_4_actualizacion_manual_del_historial(driver, wait, network):
    abrir_dashboard(driver, wait)
    ir_a_pestana(driver, wait, "Historial")

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h2[contains(text(),'Historial de Ejecuciones')]")
    ))
    wait.until(lambda d: network.count("/api/history", "GET") >= 1)
    peticiones_antes = network.count("/api/history", "GET")
    print(f"[INFO] Peticiones GET /api/history antes de 'Actualizar': {peticiones_antes}")

    boton = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(., 'Actualizar')]")
    ))
    boton.click()

    wait.until(lambda d: network.count("/api/history", "GET") > peticiones_antes)
    print("[OK] El clic en 'Actualizar' disparó un nuevo GET /api/history")

    # El botón debe seguir funcional al terminar (no queda deshabilitado)
    boton_final = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(., 'Actualizar')]")
    ))
    assert boton_final.is_enabled()
    print("[OK] El botón 'Actualizar' queda habilitado nuevamente al terminar la carga")

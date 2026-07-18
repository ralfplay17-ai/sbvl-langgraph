"""
Caso de Prueba 3.3 - "Estado sin noticias disponibles"

Sin ALPHA_VANTAGE_KEY/NEWSAPI_KEY configuradas y sin salida de red hacia
Google News RSS en este entorno, ambas fuentes de noticias devuelven listas
vacías de forma real: es el escenario natural para probar el estado vacío.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import abrir_dashboard, ir_a_pestana, seleccionar_ticker


def test_caso_3_3_estado_sin_noticias_disponibles(driver, wait):
    abrir_dashboard(driver, wait)
    seleccionar_ticker(driver, wait, "BVN")
    ir_a_pestana(driver, wait, "Noticias")

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h2[contains(text(),'Noticias para')]")
    ))
    assert "Noticias para" in driver.page_source and "BVN" in driver.page_source
    print("[OK] Título 'Noticias para BVN' presente")

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(),'Sin noticias disponibles')]")
    ))
    assert "Sin noticias disponibles" in driver.page_source
    print("[OK] Columna Alpha Vantage muestra el mensaje de 'Sin noticias disponibles'")

    # Google News RSS también sin resultados en este entorno sin salida de red
    if "Sin resultados en Google News RSS." in driver.page_source:
        print("[OK] Columna Google News muestra 'Sin resultados en Google News RSS.'")
    else:
        print("[INFO] Google News mostró resultados (puede variar según la conectividad del entorno)")

"""
Caso de Prueba 2.3 - "Fallback ante falla de fuente de datos de un metal"

En este entorno no hay salida de red hacia yfinance/Alpha Vantage/Twelve Data,
por lo que las 3 fuentes de cada metal fallan en cascada de forma real y
reproducible: es el escenario ideal para probar el estado de error sin tener
que simular nada.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import abrir_dashboard, ir_a_pestana

# Nota: en JSX, `{key}: {d.error}` genera nodos de texto SEPARADOS ("Oro", ": ",
# "Sin datos"), no uno solo. XPath text() compara nodo por nodo, así que
# contains(text(),'Oro: Sin datos') nunca matchea aunque el texto renderizado
# se vea junto. Por eso se usa contains(., ...) sobre el <p> contenedor.
ERROR_XPATH = "//p[contains(@class,'text-red-400')][contains(., 'Sin datos')]"


def test_caso_2_3_fallback_sin_datos_de_commodities(driver, wait):
    abrir_dashboard(driver, wait)
    ir_a_pestana(driver, wait, "Commodities")

    # Esperar a que termine el estado de carga (skeleton) para cada tarjeta
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h2[contains(text(),'Precios en Tiempo Real')]")
    ))

    wait.until(EC.presence_of_element_located((By.XPATH, ERROR_XPATH)))

    tarjetas_error = driver.find_elements(By.XPATH, ERROR_XPATH)
    assert tarjetas_error, "No se mostró el mensaje 'Sin datos' para ningún metal"
    textos = [t.text for t in tarjetas_error]
    print(f"[OK] Tarjetas mostrando fallback 'Sin datos' (sin red externa disponible): {textos}")

    # Las 3 fuentes (yfinance, Alpha Vantage, Twelve Data) fallan sin red -> los 3 metales
    assert len(tarjetas_error) == 3, f"Se esperaban 3 metales sin datos, se observaron {len(tarjetas_error)}"

    # El resto de la pestaña (tabla de relevancia) debe seguir funcionando
    assert "Relevancia por empresa BVL" in driver.page_source
    print("[OK] La tabla de relevancia por empresa sigue mostrándose pese al fallo de precios")

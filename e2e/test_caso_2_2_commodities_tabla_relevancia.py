"""
Caso de Prueba 2.2 - "Tabla de relevancia por empresa BVL"

Datos estáticos (no dependen de red externa), por lo que es 100% determinista.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import abrir_dashboard, ir_a_pestana

EMPRESAS_ESPERADAS = [
    "BVN (Buenaventura)",
    "SCCO (Southern Copper)",
    "CVERDEC1 (Cerro Verde)",
    "MINSURI1 (Minsur)",
    "VOLCABC1 (Volcan)",
    "BROCALC1 (El Brocal)",
    "NEXAPEC1 (Nexa)",
]


def test_caso_2_2_tabla_relevancia_por_empresa_bvl(driver, wait):
    abrir_dashboard(driver, wait)
    ir_a_pestana(driver, wait, "Commodities")

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h3[contains(text(),'Relevancia por empresa BVL')]")
    ))

    filas = driver.find_elements(By.XPATH, "//h3[contains(text(),'Relevancia por empresa BVL')]/following::table[1]/tbody/tr")
    assert len(filas) == 7, f"Se esperaban 7 filas en la tabla de relevancia, se encontraron {len(filas)}"
    print(f"[OK] La tabla de relevancia tiene {len(filas)} filas")

    texto_tabla = driver.find_element(
        By.XPATH, "//h3[contains(text(),'Relevancia por empresa BVL')]/following::table[1]"
    ).text
    for empresa in EMPRESAS_ESPERADAS:
        assert empresa in texto_tabla, f"No se encontró '{empresa}' en la tabla de relevancia"
    print("[OK] Las 7 empresas mineras esperadas están presentes en la tabla")

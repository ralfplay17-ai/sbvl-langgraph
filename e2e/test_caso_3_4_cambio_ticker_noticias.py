"""
Caso de Prueba 3.4 - "Cambio de ticker recarga las noticias"

Verifica, a nivel de red (CDP), que cambiar el ticker en el Sidebar dispara
un nuevo GET /api/market/noticias/{ticker} para el ticker nuevo -- prueba el
useEffect con dependencia [ticker] en NewsTab.tsx sin depender de que haya
contenido real (no hay claves de Alpha Vantage/NewsAPI ni red externa en
este entorno, ver caso 3.3).
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import abrir_dashboard, ir_a_pestana, seleccionar_ticker


def test_caso_3_4_cambio_de_ticker_recarga_las_noticias(driver, wait, network):
    abrir_dashboard(driver, wait)
    seleccionar_ticker(driver, wait, "BVN")
    ir_a_pestana(driver, wait, "Noticias")

    wait.until(EC.presence_of_element_located((By.XPATH, "//h2[contains(text(),'Noticias para')]")))
    wait.until(lambda d: network.count("/api/market/noticias/BVN", "GET") >= 1)
    print("[OK] Al entrar a la pestaña Noticias con BVN se pidió GET /api/market/noticias/BVN")

    # Cambiar el ticker mientras la pestaña Noticias sigue activa
    seleccionar_ticker(driver, wait, "SCCO")

    wait.until(EC.text_to_be_present_in_element(
        (By.XPATH, "//h2[contains(text(),'Noticias para')]"), "SCCO"
    ))
    print("[OK] El título cambia a 'Noticias para SCCO'")

    wait.until(lambda d: network.count("/api/market/noticias/SCCO", "GET") >= 1)
    print("[OK] El cambio de ticker disparó un nuevo GET /api/market/noticias/SCCO")

    # No debió haberse pedido un segundo GET para BVN después del cambio
    assert network.count("/api/market/noticias/BVN", "GET") == 1
    print("[OK] No se repitió el fetch de BVN tras cambiar a SCCO")

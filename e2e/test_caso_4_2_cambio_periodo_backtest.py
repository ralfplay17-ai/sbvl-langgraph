"""
Caso de Prueba 4.2 - "Cambio de período de backtest"

Es un caso puramente de UI (no depende de datos de mercado): verifica que
al hacer clic en un período distinto, ese botón queda resaltado (activo) y
el resto se deselecciona. El período "3 meses (90 días)" es el default.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from conftest import abrir_dashboard, ir_a_pestana


def boton_periodo(driver, label: str):
    return driver.find_element(By.XPATH, f"//button[contains(., '{label}')]")


def esta_activo(boton) -> bool:
    return "bg-blue-600" in boton.get_attribute("class")


def test_caso_4_2_cambio_de_periodo_de_backtest(driver, wait):
    abrir_dashboard(driver, wait)
    ir_a_pestana(driver, wait, "Backtesting")

    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h2[contains(text(),'Backtesting')]")
    ))

    default_btn = boton_periodo(driver, "3 meses (90 días)")
    assert esta_activo(default_btn), "El período por defecto (90 días) debería estar activo al cargar"
    print("[OK] El período por defecto '3 meses (90 días)' está activo al cargar la pestaña")

    anio_btn = boton_periodo(driver, "1 año (365 días)")
    assert not esta_activo(anio_btn)
    anio_btn.click()

    wait.until(lambda d: esta_activo(boton_periodo(d, "1 año (365 días)")))
    print("[OK] '1 año (365 días)' queda activo tras el clic")

    default_btn = boton_periodo(driver, "3 meses (90 días)")
    assert not esta_activo(default_btn), "El período anterior debería desactivarse al elegir uno nuevo"
    print("[OK] '3 meses (90 días)' se desactiva al seleccionar otro período")

    # Repetir con los otros dos períodos restantes para cubrir los 4 botones
    for label in ["6 meses (180 días)", "5 años (OE4)"]:
        boton_periodo(driver, label).click()
        wait.until(lambda d, l=label: esta_activo(boton_periodo(d, l)))
        assert not esta_activo(boton_periodo(driver, "1 año (365 días)"))
        print(f"[OK] '{label}' queda activo tras el clic y los demás se desactivan")

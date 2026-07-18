"""Fixtures y helpers compartidos por los tests E2E (Selenium)."""
import json
import os
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:3000")
CHROME_BIN = os.environ.get("E2E_CHROME_BIN", "/opt/pw-browsers/chromium")
CHROMEDRIVER_BIN = os.environ.get("E2E_CHROMEDRIVER_BIN", "/opt/node22/bin/chromedriver")
ANALYSIS_TIMEOUT = int(os.environ.get("E2E_ANALYSIS_TIMEOUT", "120"))


@pytest.fixture
def driver():
    opts = Options()
    opts.binary_location = CHROME_BIN
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1400,1000")
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    service = Service(executable_path=CHROMEDRIVER_BIN)
    d = webdriver.Chrome(service=service, options=opts)
    d.implicitly_wait(0)
    yield d
    d.quit()


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 20)


class NetworkLog:
    """Acumula eventos Network.requestWillBeSent del log de performance de CDP.

    driver.get_log("performance") DRENA el buffer en cada llamada -- no es una
    lectura idempotente. Si se llama varias veces sueltas (p. ej. una vez
    dentro de un wait.until en polling y otra vez después), las llamadas
    posteriores solo ven eventos NUEVOS desde la última lectura, no el
    historial completo. Esta clase mantiene un acumulador propio para poder
    contar peticiones de forma confiable en cualquier momento del test.
    """

    def __init__(self, driver):
        self._driver = driver
        self._entries: list[dict] = []

    def _drain(self):
        self._entries.extend(self._driver.get_log("performance"))

    def count(self, url_substring: str, method: str | None = None) -> int:
        self._drain()
        total = 0
        for entry in self._entries:
            try:
                msg = json.loads(entry["message"])["message"]
            except (KeyError, ValueError):
                continue
            if msg.get("method") != "Network.requestWillBeSent":
                continue
            request = msg.get("params", {}).get("request", {})
            if url_substring in request.get("url", "") and (method is None or request.get("method") == method):
                total += 1
        return total


@pytest.fixture
def network(driver):
    return NetworkLog(driver)


def abrir_dashboard(driver, wait):
    driver.get(BASE_URL)
    wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(),'Dashboard BVL')]")))


def seleccionar_ticker(driver, wait, ticker: str):
    select_el = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//label[contains(text(),'Empresa / Ticker')]/following-sibling::select")
    ))
    Select(select_el).select_by_value(ticker)


def ir_a_pestana(driver, wait, label: str):
    tab = wait.until(EC.element_to_be_clickable(
        (By.XPATH, f"//button[@role='tab'][contains(., '{label}')]")
    ))
    tab.click()
    wait.until(EC.text_to_be_present_in_element_attribute(
        (By.XPATH, f"//button[@role='tab'][contains(., '{label}')]"), "data-state", "active"
    ))


def ejecutar_analisis(driver, wait):
    boton = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//aside//button[contains(., 'Ejecutar Análisis')]")
    ))
    boton.click()
    return boton


def esperar_analisis_terminado(driver, timeout=ANALYSIS_TIMEOUT):
    """Espera a que el análisis llegue a un estado terminal válido:
    señal final en el SignalBanner, o modal 'El análisis no pudo completarse'.
    Devuelve una tupla (tiene_senal, tiene_modal_error)."""
    long_wait = WebDriverWait(driver, timeout)

    def terminado(d):
        señal = d.find_elements(By.XPATH, "//*[contains(text(),'COMPRAR') or contains(text(),'MANTENER') or contains(text(),'VENDER')]")
        modal_error = d.find_elements(By.XPATH, "//*[contains(text(),'El análisis no pudo completarse')]")
        return bool(señal) or bool(modal_error)

    long_wait.until(terminado)
    page = driver.page_source
    tiene_senal = any(s in page for s in ["COMPRAR", "MANTENER", "VENDER"])
    tiene_modal_error = "El análisis no pudo completarse" in page
    return tiene_senal, tiene_modal_error


def cerrar_modal_error_si_existe(driver, wait):
    botones = driver.find_elements(By.XPATH, "//button[contains(., 'Entendido')]")
    if botones:
        botones[0].click()
        wait.until(EC.invisibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'El análisis no pudo completarse')]")
        ))

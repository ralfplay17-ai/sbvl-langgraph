# Tests E2E (Selenium WebDriver)

Pruebas de extremo a extremo que manejan un navegador real contra el
dashboard corriendo (frontend + backend), a diferencia de `backend/tests/`
que son tests unitarios/de integración con mocks.

## Casos cubiertos

| Archivo | Caso (ver `casos_de_prueba_SBVL.xlsx`) | Qué valida |
|---|---|---|
| `test_caso_1_1_analisis_selenium.py` | 1.1 | Flujo completo: seleccionar ticker, ejecutar análisis, llegar a un estado terminal (señal o modal de error), botón se rehabilita. |
| `test_caso_1_2_cambio_ticker.py` | 1.2 | Cambiar de ticker resetea el estado previo (result/events) y dispara un nuevo fetch de precio para el ticker nuevo. |
| `test_caso_1_5_doble_ejecucion.py` | 1.5 | Un doble clic rápido en "Ejecutar Análisis" dispara **una sola** petición `POST /api/analyze` (verificado a nivel de red vía CDP, no solo mirando el DOM). |
| `test_caso_2_2_commodities_tabla_relevancia.py` | 2.2 | Tabla estática de relevancia por empresa BVL (7 filas). |
| `test_caso_2_3_commodities_sin_datos.py` | 2.3 | Fallback a "Sin datos" cuando fallan las 3 fuentes de precio de un metal. |
| `test_caso_3_3_noticias_sin_datos.py` | 3.3 | Estado vacío de noticias cuando no hay resultados en Alpha Vantage ni Google News RSS. |
| `test_caso_5_5_historial_vacio.py` | 5.5 | Estado vacío del historial cuando no hay ejecuciones registradas. |

Los casos 1.3 y 4.3 (validación de rangos de PSO/backtest) **no** se automatizan
acá porque el propio frontend ya limita esos valores (sliders/botones fijos):
solo son alcanzables llamando directamente a la API (ver `casos_de_prueba_SBVL.xlsx`).

## Prerequisitos

1. Backend corriendo en `http://localhost:8000`:
   ```bash
   cd backend
   source venv/bin/activate   # o el entorno que uses
   uvicorn main:app --port 8000
   ```
2. Frontend corriendo en `http://localhost:3000`:
   ```bash
   cd frontend
   npm run dev
   ```
3. Dependencias de este directorio:
   ```bash
   pip install -r e2e/requirements.txt
   ```
4. Un Chrome/Chromium instalado y un `chromedriver` de **la misma versión
   mayor**. Si `chromedriver --version` no coincide con el Chrome instalado,
   Selenium falla con `SessionNotCreatedException`. Se puede indicar
   explícitamente con variables de entorno (ver abajo).

## Ejecutar

```bash
pytest e2e/ -v -s
```

o un caso puntual:

```bash
pytest e2e/test_caso_1_1_analisis_selenium.py -v -s
```

### Variables de entorno soportadas

| Variable | Default | Descripción |
|---|---|---|
| `E2E_BASE_URL` | `http://localhost:3000` | URL del frontend |
| `E2E_CHROME_BIN` | `/opt/pw-browsers/chromium` | Binario de Chrome/Chromium |
| `E2E_CHROMEDRIVER_BIN` | `/opt/node22/bin/chromedriver` | Binario de chromedriver |
| `E2E_ANALYSIS_TIMEOUT` | `120` | Segundos máximos a esperar el resultado del análisis |

## Notas de comportamiento real observadas al construir estos tests

- **Sin `DEEPSEEK_API_KEY` configurada**, `get_llm()` (`backend/config.py`) lanza
  `OpenAIError` de forma **síncrona**, y esa llamada ocurre en
  `agentes_paralelo()` (`backend/agents/graph.py`) **antes** del `try/except`
  que degrada cada agente individualmente a `MANTENER`. Es decir: sin
  credenciales, el grafo completo aborta con un evento SSE `"error"` y
  **nunca llega a emitir `"final"`** -- `result` nunca se puebla en el
  frontend, a diferencia de cuando un agente individual falla en tiempo de
  ejecución (con credenciales válidas pero, por ejemplo, una fuente de datos
  caída), que sí degrada por-agente y produce un resultado final con
  `error_sistema` poblado. `test_caso_1_1_*` y `test_caso_1_2_*` contemplan
  ambos caminos.
- **CORS preflight**: el frontend (`:3000`) llama al backend (`:8000`), origen
  cruzado con `Content-Type: application/json` → el navegador manda un
  `OPTIONS /api/analyze` antes del `POST /api/analyze` real. Si se cuentan
  peticiones de red por URL sin filtrar por método HTTP, cualquier análisis
  (incluso uno solo) cuenta como "2 peticiones" a `/api/analyze`. Ver
  `contar_requests_analyze()` en `test_caso_1_5_doble_ejecucion.py`.
- **XPath `text()` vs JSX**: cuando el JSX interpola texto como
  `{variable}: {otraVariable}`, React genera nodos de texto **separados**
  (uno por expresión), no uno solo concatenado. `contains(text(), 'Oro: Sin
  datos')` nunca matchea aunque se vea junto en pantalla; hay que usar
  `contains(., '...')` sobre el elemento contenedor. Ver `test_caso_2_3_*`.
- Este sandbox no tiene salida de red hacia yfinance/BVL/Alpha Vantage/Google
  News, lo cual en la práctica hace que los casos 2.3, 3.3 y 5.5 sean
  deterministas aquí (las fuentes externas siempre fallan). Con red real y/o
  claves configuradas, esos mismos endpoints devolverían datos reales y esas
  aserciones de "estado vacío" no aplicarían tal cual.

## Por qué viven fuera de `backend/tests/`

Estos tests **no** se ejecutan como parte de `pytest tests/ -v` (backend):
requieren un navegador real y los dos servidores arriba, cosa que no aplica
a un run normal de tests unitarios/CI sin ese entorno.

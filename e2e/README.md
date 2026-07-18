# Tests E2E (Selenium WebDriver + validación de API)

Pruebas de extremo a extremo que manejan un navegador real contra el
dashboard corriendo (frontend + backend), a diferencia de `backend/tests/`
que son tests unitarios/de integración con mocks.

## Casos cubiertos (13 de los 25 de `casos_de_prueba_SBVL.xlsx`, + 1 extra)

| Archivo | Caso | Tipo | Qué valida |
|---|---|---|---|
| `test_caso_1_1_analisis_selenium.py` | 1.1 | Selenium | Flujo completo: seleccionar ticker, ejecutar análisis, llegar a un estado terminal (señal o modal de error), botón se rehabilita. |
| `test_caso_1_2_cambio_ticker.py` | 1.2 | Selenium | Cambiar de ticker resetea el estado previo (result/events) y dispara un nuevo fetch de precio para el ticker nuevo. |
| `test_caso_1_3_pso_validacion_api.py` | 1.3 | API (requests) | `POST /api/analyze` rechaza con 422 valores de PSO fuera de rango; acepta los válidos. |
| `test_caso_1_5_doble_ejecucion.py` | 1.5 | Selenium | Un doble clic rápido en "Ejecutar Análisis" dispara **una sola** petición `POST /api/analyze` (verificado a nivel de red vía CDP, no solo mirando el DOM). |
| `test_caso_2_2_commodities_tabla_relevancia.py` | 2.2 | Selenium | Tabla estática de relevancia por empresa BVL (7 filas). |
| `test_caso_2_3_commodities_sin_datos.py` | 2.3 | Selenium | Fallback a "Sin datos" cuando fallan las 3 fuentes de precio de un metal. |
| `test_caso_3_3_noticias_sin_datos.py` | 3.3 | Selenium | Estado vacío de noticias cuando no hay resultados en Alpha Vantage ni Google News RSS. |
| `test_caso_3_4_cambio_ticker_noticias.py` | 3.4 | Selenium | Cambiar de ticker en la pestaña Noticias dispara un nuevo fetch para el ticker nuevo (y no repite el anterior). |
| `test_caso_4_2_cambio_periodo_backtest.py` | 4.2 | Selenium | Los 4 botones de período (90/180/365/1825 días) se resaltan como activos/inactivos correctamente al hacer clic. |
| `test_caso_4_3_backtest_validacion_api.py` | 4.3 | API (requests) | `POST /api/backtest` rechaza con 422 `dias` fuera de [30, 1825]; acepta los válidos. |
| `test_caso_5_4_actualizacion_manual_historial.py` | 5.4 | Selenium | El botón "Actualizar" dispara un nuevo `GET /api/history`. |
| `test_caso_5_5_historial_vacio.py` | 5.5 | Selenium | Estado vacío del historial cuando no hay ejecuciones registradas. |
| `test_extra_backtest_falla_gracefully.py` | *(extra, complementa 4.1)* | Selenium | El backtest sin datos de mercado muestra el error real en la UI en vez de colgarse o inventar métricas. |

### Casos NO automatizados aquí (por qué)

- **1.4** (falla de un agente individual) ya está cubierto a nivel de integración
  por `backend/tests/test_graph.py::test_grafo_degrada_cuando_un_agente_falla`.
  Reproducirlo end-to-end por navegador requeriría credenciales de LLM reales
  *más* forzar el fallo de un solo agente (p. ej. apagar solo una fuente de
  datos), algo que no se puede lograr solo con variables de entorno en este
  backend corriendo en un único proceso.
- **2.1, 2.4, 2.5** (precios reales de metales, sparkline, colores por
  variación), **3.1, 3.2, 3.5** (noticias reales, sentimiento, enlaces),
  **4.1, 4.4, 4.5** (backtest con métricas reales), **5.1, 5.2, 5.3**
  (historial con registros reales) requieren datos reales de mercado/noticias
  y, para 5.1-5.3, un Supabase configurado con al menos una ejecución
  guardada. Ninguno es reproducible en este sandbox (sin salida de red externa
  ni credenciales) de forma determinista; con `backend/.env` completo y acceso
  a internet, son automatizables con el mismo patrón que los casos existentes.

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

Los tests API-only (`test_caso_1_3_*`, `test_caso_4_3_*`) no necesitan
navegador ni chromedriver, solo el backend corriendo -- pueden filtrarse con:

```bash
pytest e2e/ -v -k "api"
```

### Variables de entorno soportadas

| Variable | Default | Descripción |
|---|---|---|
| `E2E_BASE_URL` | `http://localhost:3000` | URL del frontend |
| `E2E_API_URL` | `http://localhost:8000` | URL del backend (tests API-only) |
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
  (incluso uno solo) cuenta como "2 peticiones" a `/api/analyze`.
- **`driver.get_log("performance")` DRENA el buffer en cada llamada** -- no es
  una lectura idempotente. Si se necesita contar peticiones de red en más de
  un momento del mismo test (p. ej. antes y después de una acción), hay que
  acumular las lecturas en vez de comparar snapshots sueltos. Ver la clase
  `NetworkLog` / fixture `network` en `conftest.py` (usada por los casos 1.2,
  1.5, 3.4 y 5.4).
- **XPath `text()` vs JSX**: cuando el JSX interpola texto como
  `{variable}: {otraVariable}`, React genera nodos de texto **separados**
  (uno por expresión), no uno solo concatenado. `contains(text(), 'Oro: Sin
  datos')` nunca matchea aunque se vea junto en pantalla; hay que usar
  `contains(., '...')` sobre el elemento contenedor. Ver `test_caso_2_3_*`.
- Este sandbox no tiene salida de red hacia yfinance/BVL/Alpha Vantage/Google
  News, lo cual en la práctica hace que los casos 2.3, 3.3, 5.5 y el extra de
  backtest sean deterministas aquí (las fuentes externas siempre fallan). Con
  red real y/o claves configuradas, esos mismos endpoints devolverían datos
  reales y esas aserciones de "estado vacío"/"sin datos" no aplicarían tal cual.

## Por qué viven fuera de `backend/tests/`

Estos tests **no** se ejecutan como parte de `pytest tests/ -v` (backend):
requieren un navegador real y los dos servidores arriba, cosa que no aplica
a un run normal de tests unitarios/CI sin ese entorno.

# Pruebas de integración (frontend ↔ backend)

Estas pruebas llaman **directamente a las funciones reales de `lib/api.ts`**
(las que usan los componentes React) contra un **backend FastAPI real**
corriendo — sin mockear `fetch`, sin navegador. Verifican el contrato de
datos entre ambos lados: forma del JSON, parseo, manejo de errores HTTP y,
en el caso de `streamAnalysis()`, el parseo manual de Server-Sent Events
línea por línea contra bytes reales del stream.

Se diferencian de:
- **`backend/tests/`** (pytest, unitario/integración solo del lado backend, con mocks de red externa).
- **`e2e/`** (Selenium, integración a través de un navegador real y el DOM).

Esta capa es más rápida que Selenium (no levanta navegador) y prueba algo que
ni el backend solo ni el E2E prueban directamente: que el **código TypeScript
que consume la API** (`lib/api.ts`) interpreta correctamente las respuestas
reales del backend.

## Prerequisitos

Backend corriendo en `http://localhost:8000` (o el que indique
`NEXT_PUBLIC_API_URL`):

```bash
cd backend
source venv/bin/activate
uvicorn main:app --port 8000
```

## Ejecutar

```bash
cd frontend
npm run test:integration
```

## Qué cubre cada archivo

| Archivo | Qué prueba |
|---|---|
| `market.integration.test.ts` | `getTickers`, `getPrecio`, `getHistorico`, `getCommodities`, `getNoticias` — forma de la respuesta en éxito y en degradado (`{error}`). |
| `backtest.integration.test.ts` | `runBacktest` — forma del resultado, y que un 422 real de Pydantic (`dias` fuera de rango) se propaga como excepción. |
| `history.integration.test.ts` | `getHistory` — siempre array, filtro por ticker, respeta `limit`. |
| `analyze-sse.integration.test.ts` | `streamAnalysis` — el parseo manual de SSE contra el stream real de `POST /api/analyze` (orden de eventos, evento `close` final, JSON válido). |
| `error-handling.integration.test.ts` | Que los helpers `get`/`post` privados lanzan `Error` con el código HTTP real en errores 422/404. |

## Notas

- Sin `DEEPSEEK_API_KEY` ni salida de red externa (como en este sandbox),
  varios endpoints devuelven una forma "degradada" (`{error: "..."}` o listas
  vacías) en vez de datos reales. Los tests están escritos para aceptar
  **ambos** caminos válidos (éxito real o degradado), ya que el objetivo es
  verificar el contrato de datos, no la disponibilidad de fuentes externas.
- `analyze-sse.integration.test.ts` usa un timeout interno de 15s por test
  (menor al timeout global de Vitest de 30s) y un `afterEach` que siempre
  aborta la conexión SSE activa. Se detectó en la práctica que si el timeout
  interno es mayor al de Vitest, Vitest mata el test primero sin llamar al
  cleanup, dejando el stream HTTP abierto y colgando el proceso —
  importante mantener siempre `timeoutMs` de la prueba por debajo de
  `testTimeout` de `vitest.integration.config.ts`.

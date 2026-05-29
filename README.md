# Sistema Multiagente BVL

Sistema de soporte a decisiones de inversión en acciones mineras de la Bolsa de Valores de Lima (BVL), basado en un grafo multiagente con PSO Consensus Engine.

## Stack

| Capa | Tecnología |
|---|---|
| Orquestación | LangGraph |
| LLM | DeepSeek (`deepseek-chat`) |
| API | FastAPI |
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Base de datos | Supabase (opcional) |

## Arquitectura

```
Usuario → FastAPI → LangGraph
                      ├── Agente Técnico     (Alpha Vantage / BVL)
                      ├── Agente Commodities  (Twelve Data / Alpha Vantage)
                      ├── Agente Sentimiento  (Alpha Vantage News)
                      └── Agente Riesgo       (BCRP API)
                              ↓
                      PSO Consensus Engine   (PySwarms GlobalBestPSO)
                              ↓
                      Agente Coordinador
                              ↓
                      Respuesta final → Frontend React
```

## Inicio rápido

### 1. Variables de entorno

```bash
cp .env.example .env
# Editar .env con tus API keys
```

### 2. Modo desarrollo

```bash
# Instalar dependencias
make install

# Terminal 1 — backend (http://localhost:8000)
make dev-backend

# Terminal 2 — frontend (http://localhost:5173)
make dev-frontend
```

### 3. Docker

```bash
make build
make up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## Estructura

```
├── backend/
│   ├── agents/       — 4 agentes especializados + coordinador
│   ├── api/          — FastAPI: endpoints y routers
│   ├── db/           — Cliente Supabase (opcional)
│   ├── graph/        — Grafo LangGraph (paralelismo + PSO)
│   ├── pso/          — PSO Consensus Engine (PySwarms)
│   └── tools/        — Herramientas de datos externos
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/    — Dashboard, Backtesting
│       ├── lib/      — Cliente HTTP
│       └── types/
├── Dockerfile        — Imagen backend
├── docker-compose.yml
└── railway.toml      — Deploy en Railway
```

## API

| Endpoint | Descripción |
|---|---|
| `GET /health` | Estado del servidor |
| `POST /analysis/run` | Ejecutar análisis multiagente |
| `GET /analysis/history` | Historial de análisis |
| `POST /backtest/run` | Backtesting histórico |
| `GET /docs` | Documentación interactiva |

## Acciones soportadas

- **BVN** — Compañía de Minas Buenaventura (commodity: Oro)
- **SCCO** — Southern Copper Corporation (commodity: Cobre)

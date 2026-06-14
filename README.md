# SBVL-LangGraph — Sistema de Análisis Multia-gente para la BVL

Dashboard de análisis de acciones mineras de la **Bolsa de Valores de Lima (BVL)** impulsado por un sistema de agentes LLM coordinados con **LangGraph** y consenso por **PSO (Particle Swarm Optimization)**.

---

## Qué hace

Dado un ticker de la BVL (ej. `SCCO`, `BVN`), el sistema lanza 4 agentes LLM en paralelo, cada uno analizando una dimensión distinta:

| Agente | Análisis |
|---|---|
| **Técnico** | RSI, MACD, SMA sobre precios históricos |
| **Commodities** | Tendencia de Oro, Plata y Cobre |
| **Sentimiento** | Noticias y sentimiento de prensa |
| **Riesgo** | Tipo de cambio USD/PEN, tasas BCRP |

Los 4 scores (`-1.0` → `+1.0`) son combinados por un optimizador PSO que encuentra los pesos óptimos para cada agente. El resultado es una señal consolidada **COMPRAR / MANTENER / VENDER** con nivel de confianza.

El proceso se transmite en tiempo real vía **Server-Sent Events (SSE)** al dashboard.

---

## Arquitectura

```
┌─────────────────────────────────────────────────┐
│  Next.js Frontend (Vercel)                       │
│  Tabs: Análisis · Commodities · Noticias · BT    │
└──────────────────┬──────────────────────────────┘
                   │ SSE + REST
┌──────────────────▼──────────────────────────────┐
│  FastAPI Backend (Railway)                       │
│                                                  │
│  LangGraph Workflow:                             │
│   1. agentes_paralelo  ──→ 4 agentes en async   │
│   2. pso_consensus     ──→ PySwarms optimiza     │
│   3. coordinador       ──→ resultado final       │
│                                                  │
│  API adicional:                                  │
│   /market/*  precios, histórico, noticias        │
│   /backtest  validación histórica de estrategia  │
│   /history   historial en Supabase               │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  Supabase (PostgreSQL)                           │
│  Tabla: analysis_history                         │
└─────────────────────────────────────────────────┘
```

### Fuentes de datos

| Dato | Fuente primaria | Fallback 1 | Fallback 2 |
|---|---|---|---|
| Precio acción BVL | BVL API (dataondemand) | — | — |
| OHLC histórico | yfinance | Twelve Data | — |
| Commodities | yfinance futuros (GC=F, SI=F, HG=F) | Alpha Vantage FX | Twelve Data ETFs (GLD, SLV, COPX) |
| Noticias | Alpha Vantage News | Google News RSS | NewsAPI |
| Macro (USD/PEN, tasas) | BCRP API | — | — |

---

## Stack tecnológico

**Backend**
- Python 3.10+, FastAPI 0.115
- LangChain 0.3 + LangGraph 0.2 (orquestación de agentes)
- DeepSeek API como LLM (compatible con OpenAI SDK)
- PySwarms (PSO)
- Pandas, NumPy, yfinance

**Frontend**
- Next.js 15.3.9 + React 19 + TypeScript 5.7
- Radix UI + Tailwind CSS
- ECharts (gráficos de velas, capital, convergencia PSO)

**Infraestructura**
- Railway (backend)
- Vercel (frontend)
- Supabase (PostgreSQL)

---

## Variables de entorno

### Backend (`backend/.env`)

```env
# LLM
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat

# Datos de mercado
ALPHA_VANTAGE_KEY=         # https://www.alphavantage.co/support/#api-key
TWELVEDATA_KEY=            # https://twelvedata.com/pricing
NEWSAPI_KEY=               # https://newsapi.org/register

# Base de datos
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

# CORS (separados por comas)
ALLOWED_ORIGINS=http://localhost:3000,https://tu-dominio.vercel.app
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Instalación local

### Prerequisitos

- Python 3.10+
- Node.js 18+
- Cuenta en Supabase con las migraciones aplicadas

### Base de datos

Ejecutar las migraciones en Supabase (SQL editor o CLI):

```bash
# Con Supabase CLI
supabase db push

# O manualmente: copiar y ejecutar el contenido de
# supabase/migrations/001_init.sql
```

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Editar .env con tus claves

uvicorn main:app --reload --port 8000
```

API disponible en `http://localhost:8000`. Documentación en `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local
# Editar: NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
```

Dashboard disponible en `http://localhost:3000`.

---

## Despliegue en producción

### Supabase

1. Crear proyecto en [supabase.com](https://supabase.com)
2. Ejecutar `supabase/migrations/001_init.sql` en el SQL Editor

### Railway (backend)

1. Conectar el repositorio en [railway.app](https://railway.app)
2. Establecer root directory: `backend/`
3. Agregar todas las variables de entorno del backend
4. Railway detecta `railway.toml` y usa nixpacks automáticamente

### Vercel (frontend)

1. Importar el repositorio en [vercel.com](https://vercel.com)
2. Establecer root directory: `frontend/`
3. Agregar variable de entorno:
   - `NEXT_PUBLIC_API_URL` → URL pública de Railway
4. Vercel detecta Next.js y despliega automáticamente

---

## Estructura del proyecto

```
sbvl-langgraph/
├── backend/
│   ├── agents/             # Agentes LLM + grafo LangGraph
│   │   ├── graph.py        # Workflow: paralelo → PSO → coordinador
│   │   ├── state.py        # TypedDict del estado compartido
│   │   ├── tecnico.py      # Agente de análisis técnico
│   │   ├── commodities.py  # Agente de commodities
│   │   ├── sentimiento.py  # Agente de sentimiento
│   │   ├── riesgo.py       # Agente de riesgo macro
│   │   └── utils.py        # parse_agent_result con Pydantic
│   ├── api/                # Rutas FastAPI
│   │   ├── analyze.py      # POST /api/analyze (SSE)
│   │   ├── backtest.py     # POST /api/backtest
│   │   ├── market.py       # GET /market/* (precios, noticias)
│   │   └── history.py      # GET /api/history
│   ├── core/
│   │   ├── indicators.py   # RSI, MACD, SMA
│   │   └── backtest.py     # Motor de backtesting
│   ├── pso/
│   │   └── consensus.py    # Optimización PSO con PySwarms
│   ├── tools/              # Herramientas LangChain para los agentes
│   ├── db/
│   │   └── supabase.py     # Cliente Supabase
│   ├── tests/              # Tests unitarios (pytest)
│   ├── config.py           # Settings con Pydantic + get_llm()
│   ├── main.py             # FastAPI app
│   ├── requirements.txt
│   └── railway.toml
├── frontend/
│   ├── app/
│   │   ├── page.tsx        # Dashboard principal
│   │   └── layout.tsx
│   ├── components/
│   │   ├── charts/         # ECharts: velas, backtest, sparkline
│   │   ├── dashboard/      # SignalBanner, AgentCard, PSOConfig
│   │   ├── layout/         # Sidebar
│   │   └── tabs/           # AnalysisTab, CommoditiesTab, NewsTab, BacktestTab
│   ├── lib/
│   │   ├── api.ts          # Cliente REST + SSE stream
│   │   └── types.ts        # TypeScript types
│   └── vercel.json
└── supabase/
    └── migrations/
        └── 001_init.sql    # Tabla analysis_history + índices
```

---

## Tests

```bash
cd backend
pytest tests/ -v
```

Cubre: parsing de output de agentes (10 casos), indicadores técnicos RSI/MACD/SMA (13 casos).

---

## Tickers disponibles

16 empresas mineras listadas en la BVL:

`BVN` · `SCCO` · `CVERDEC1` · `MINSURI1` · `VOLCABC1` · `NEXAPEC1` · `BROCALC1` · `SHPC1` · `PODERC1` · `MOROCOC1` · `LUISAI1` · `ATACOBC1` · `MINCORC1` · `PERUBAI1` · `FOSPACC1` · `CASTROC1`

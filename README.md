# Sistema Multiagente para Inversión en Mineras BVL

Dashboard de soporte a la toma de decisiones basado en Swarm Intelligence (PSO) con dos vistas: análisis en vivo y backtesting histórico.

## Vistas

### Análisis en Vivo
- Orquestación multiagente vía Langflow (4 agentes especializados + coordinador PSO)
- Señal consolidada: COMPRAR / MANTENER / VENDER con score y confianza
- Gráfico interactivo de precio con SMA20, SMA50, RSI (14) y MACD
- Panel de estado de agentes con pesos optimizados por PSO
- Modo comparación simultánea BVN vs SCCO

### Backtesting
- Datos históricos desde BVL (fallback: Alpha Vantage)
- Simula estrategia PSO (señales por RSI + MACD + SMA) vs Buy & Hold
- Períodos: 3, 6 o 12 meses
- Métricas: retorno total, Sharpe ratio, max drawdown, win rate, nº operaciones
- Gráfico comparativo de curvas de capital

## Agentes

| Agente | Especialización |
|---|---|
| Técnico | Indicadores de precio y volumen |
| Commodities | Precio del cobre y materias primas |
| Sentimiento | Noticias y prensa financiera |
| Riesgo | Tipo de cambio y factores macro |
| Coordinador (PSO) | Consenso ponderado con 50 partículas, 100 iteraciones |

## Tecnologías

- **Streamlit** — interfaz web
- **Langflow** — orquestación de agentes IA
- **DeepSeek API** — modelo LLM de los agentes
- **Alpha Vantage** — datos históricos de precios
- **PySwarms (GlobalBestPSO)** — optimización de pesos de agentes
- **Plotly** — gráficos interactivos
- **Pandas** — procesamiento de series temporales
- **Cloudflare Tunnel** — acceso público seguro sin exponer puertos

## Estructura

```
sistema-bvl-cloud/
├── app.py                    # Dashboard Streamlit
├── sistema_bvl.json          # Flow multiagente (LangFlow)
├── start.sh                  # Entrypoint del contenedor LangFlow
├── Dockerfile                # Imagen LangFlow + agentes
├── Dockerfile.streamlit      # Imagen Streamlit
├── docker-compose.yml        # Servicios: langflow, streamlit, cloudflared
├── docker-compose.override.yml  # Puertos locales para desarrollo
├── cloudflared/
│   └── config.yml            # Rutas del túnel Cloudflare
├── data_bvl/                 # Módulo de datos BVL (scraper + CSV cache)
│   ├── bvl_data.py
│   ├── api_scraper.py
│   ├── analytics.py
│   ├── config.py
│   ├── storage.py
│   └── main.py
├── requirements.txt          # Dependencias Streamlit
└── .env.example              # Variables de entorno requeridas
```

## Despliegue con Docker

```bash
# Copiar y completar variables de entorno
cp .env.example .env

# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Variables de entorno (.env)

```
DEEPSEEK_API_KEY=tu_clave_deepseek
CLOUDFLARE_TUNNEL_TOKEN=tu_token_cloudflare
```

## Autor

Ramiro Alfaro Honores — UPAO, 2026

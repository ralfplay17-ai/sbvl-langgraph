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
- Descarga datos históricos desde Alpha Vantage (Daily Time Series)
- Simula estrategia PSO (señales por RSI + MACD + SMA) vs Buy & Hold
- Períodos: 3, 6 o 12 meses
- Métricas: retorno total, Sharpe ratio, max drawdown, win rate, nº operaciones
- Gráfico comparativo de curvas de capital
- Historial de operaciones en tabla

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
- **DeepSeek API** — modelo LLM de los agentes (via Langflow)
- **Alpha Vantage** — datos históricos de precios (backtesting e indicadores)
- **PySwarms (GlobalBestPSO)** — optimización de pesos de agentes
- **Plotly** — gráficos interactivos (precio, RSI, MACD, curvas de capital)
- **Pandas** — procesamiento de series temporales
- **NewsAPI / BCRP API** — datos macro y sentimiento (via Langflow)

## Ejecución
```bash
streamlit run app.py
```

Requiere Langflow corriendo en `localhost:7860` con el flujo multiagente importado.

## Autor
Ramiro Alfaro Honores — UPAO, Junio 2026

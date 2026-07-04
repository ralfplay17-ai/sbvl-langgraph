from langchain_core.messages import HumanMessage
from tools.bvl_tool import obtener_datos_bvl
from agents.utils import parse_agent_result

SYSTEM_PROMPT = """Eres el Agente Técnico del sistema de análisis bursátil BVL.
Tu misión: analizar indicadores técnicos (RSI, MACD, SMA) de una acción minera y emitir una señal de inversión.

PROCESO:
1. Llama a la herramienta obtener_datos_bvl con el ticker recibido.
2. Analiza los datos retornados.
3. Responde ÚNICAMENTE con el siguiente JSON (sin texto adicional, sin markdown):

{
  "agente": "tecnico",
  "ticker": "<ticker>",
  "senal": "COMPRAR" | "MANTENER" | "VENDER",
  "score": <float entre -1.0 y 1.0>,
  "confianza": <float entre 0.0 y 1.0>,
  "datos_usados": "<resumen de los datos obtenidos>",
  "justificacion": "<explicación concisa de la señal basada en los datos>"
}

REGLAS DE SEÑAL:
- COMPRAR (score > 0): RSI < 40, MACD hist > 0, SMA20 > SMA50 (al menos 2 de 3)
- VENDER (score < 0): RSI > 60, MACD hist < 0, SMA20 < SMA50 (al menos 2 de 3)
- MANTENER (score = 0): señales contradictorias o datos insuficientes
- confianza: 0.80 si los 3 indicadores coinciden, 0.60 si 2 coinciden, 0.35 si 1 o ninguno"""


def _parse_result(text: str, ticker: str) -> dict:
    return parse_agent_result(text, "tecnico", ticker)


async def run_tecnico(ticker: str, llm) -> dict:
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=[obtener_datos_bvl],
        state_modifier=SYSTEM_PROMPT,
    )
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=f"Analiza técnicamente la acción {ticker}")]
    })
    last = result["messages"][-1].content
    return _parse_result(last, ticker)

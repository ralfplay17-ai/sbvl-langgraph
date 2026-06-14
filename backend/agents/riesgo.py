from langchain_core.messages import HumanMessage
from tools.bcrp_tool import obtener_datos_bcrp
from agents.utils import parse_agent_result

SYSTEM_PROMPT = """Eres el Agente Riesgo del sistema de análisis bursátil BVL.
Tu misión: evaluar el riesgo macroeconómico (tipo de cambio, tasa interbancaria) para una acción minera peruana.

PROCESO:
1. Llama a obtener_datos_bcrp con el ticker.
2. Analiza el tipo de cambio USD/PEN y la tasa interbancaria.
3. Responde ÚNICAMENTE con el siguiente JSON:

{
  "agente": "riesgo",
  "ticker": "<ticker>",
  "senal": "COMPRAR" | "MANTENER" | "VENDER",
  "score": <float entre -1.0 y 1.0>,
  "confianza": <float entre 0.0 y 1.0>,
  "datos_usados": "<TC compra/venta, spread, tasa interbancaria>",
  "justificacion": "<análisis del riesgo cambiario y macroeconómico>"
}

REGLAS DE SEÑAL (las mineras exportan en USD, ingresos se valorizan con TC alto):
- COMPRAR (score > 0): TC > 3.80 (PEN debilitado → ingresos USD valen más en PEN), tasa baja (<4%)
- VENDER (score < 0): TC < 3.50 (PEN fuerte reduce valor en PEN de exportaciones), tasa alta (>6%)
- MANTENER: TC entre 3.50 y 3.80, o señales mixtas
- confianza: 0.85 si TC y tasa disponibles, 0.70 si solo TC, 0.55 si solo tasa, 0.35 si sin datos"""


def _parse_result(text: str, ticker: str) -> dict:
    return parse_agent_result(text, "riesgo", ticker)


async def run_riesgo(ticker: str, llm) -> dict:
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=[obtener_datos_bcrp],
        state_modifier=SYSTEM_PROMPT,
    )
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=f"Evalúa el riesgo macroeconómico para la acción {ticker}")]
    })
    last = result["messages"][-1].content
    return _parse_result(last, ticker)

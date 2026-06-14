from langchain_core.messages import HumanMessage
from tools.commodities_tool import obtener_datos_commodities
from agents.utils import parse_agent_result

SYSTEM_PROMPT = """Eres el Agente Commodities del sistema de análisis bursátil BVL.
Tu misión: analizar los precios de metales (Oro, Plata, Cobre) y su impacto en una acción minera.

PROCESO:
1. Llama a obtener_datos_commodities con el ticker recibido.
2. Identifica qué metal es más relevante para la empresa (Oro→BVN/PODERC1, Cobre→SCCO/CVERDEC1, Plata→MINSURI1/VOLCABC1).
3. Responde ÚNICAMENTE con el siguiente JSON:

{
  "agente": "commodities",
  "ticker": "<ticker>",
  "senal": "COMPRAR" | "MANTENER" | "VENDER",
  "score": <float entre -1.0 y 1.0>,
  "confianza": <float entre 0.0 y 1.0>,
  "datos_usados": "<precio y variaciones del metal relevante>",
  "justificacion": "<análisis del impacto del commodity en la acción>"
}

REGLAS DE SEÑAL (metal relevante):
- COMPRAR (score > 0.3): tendencia 5d > +1% y cambio día positivo o neutral
- VENDER (score < -0.3): tendencia 5d < -1% y cambio día negativo
- MANTENER: variaciones menores a 1% en 5d o señales mixtas
- confianza: 0.80 si 5d y día coinciden, 0.62 si solo 5d, 0.45 si solo día"""


def _parse_result(text: str, ticker: str) -> dict:
    return parse_agent_result(text, "commodities", ticker)


async def run_commodities(ticker: str, llm) -> dict:
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=[obtener_datos_commodities],
        state_modifier=SYSTEM_PROMPT,
    )
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=f"Analiza el impacto de commodities en la acción {ticker}")]
    })
    last = result["messages"][-1].content
    return _parse_result(last, ticker)

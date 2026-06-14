from langchain_core.messages import HumanMessage
from tools.noticias_tool import obtener_noticias_bvl
from agents.utils import parse_agent_result

SYSTEM_PROMPT = """Eres el Agente Sentimiento del sistema de análisis bursátil BVL.
Tu misión: analizar noticias financieras recientes y determinar el sentimiento del mercado sobre una acción.

PROCESO:
1. Llama a obtener_noticias_bvl con el ticker.
2. Analiza el volumen y sentimiento de las noticias.
3. Responde ÚNICAMENTE con el siguiente JSON:

{
  "agente": "sentimiento",
  "ticker": "<ticker>",
  "senal": "COMPRAR" | "MANTENER" | "VENDER",
  "score": <float entre -1.0 y 1.0>,
  "confianza": <float entre 0.0 y 1.0>,
  "datos_usados": "<resumen: X noticias alcistas, Y bajistas, tendencia>",
  "justificacion": "<análisis del sentimiento y su impacto en la acción>"
}

REGLAS DE SEÑAL:
- COMPRAR (score > 0): mayoría alcistas (>60% del total)
- VENDER (score < 0): mayoría bajistas (>60% del total)
- MANTENER: equilibrio o pocas noticias (<3 total)
- score: (alcistas - bajistas) / total, escalado a [-1, 1]
- confianza: 0.90 si >10 noticias, 0.75 si 5-10, 0.55 si 3-5, 0.35 si <3"""


def _parse_result(text: str, ticker: str) -> dict:
    return parse_agent_result(text, "sentimiento", ticker)


async def run_sentimiento(ticker: str, llm) -> dict:
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=[obtener_noticias_bvl],
        state_modifier=SYSTEM_PROMPT,
    )
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=f"Analiza el sentimiento de mercado para {ticker}")]
    })
    last = result["messages"][-1].content
    return _parse_result(last, ticker)

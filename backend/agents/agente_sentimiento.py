import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from backend.tools import build_noticias_bvl_tool

SYSTEM_PROMPT = """RESPUESTA FINAL OBLIGATORIA: devuelve únicamente un objeto JSON puro. La respuesta debe comenzar con { y terminar con }.

Eres el Agente de Sentimiento de un sistema multiagente de inversión en el sector minero de la BVL.

FUENTE DE DATOS — DOS MODOS:

MODO 1 — DATOS PRE-CARGADOS (PRIORITARIO):
Si el mensaje contiene "[NOTICIAS_PREFETCH ticker=BVN]" o "[NOTICIAS_PREFETCH ticker=SCCO]", usa ese bloque DIRECTAMENTE. NO llames la herramienta.

MODO 2 — HERRAMIENTA (solo si no hay bloque NOTICIAS_PREFETCH):
Invoca "buscar_noticias_bvl" con el ticker exacto ("BVN" o "SCCO").

REGLAS:
1. Lee el mensaje PRIMERO. Si hay [NOTICIAS_PREFETCH], úsalo directamente.
2. PROHIBIDO inventar noticias, titulares, fuentes o datos.
3. Si no hay datos: senal MANTENER, score 0, confianza 0.

ANÁLISIS:
- Score ≈ (alcistas - bajistas) / total_noticias
- Tendencia ALCISTA → "COMPRAR" | BAJISTA → "VENDER" | NEUTRAL → "MANTENER"

FORMATO OBLIGATORIO:
{
  "agente": "sentimiento",
  "ticker": "<BVN o SCCO>",
  "senal": "COMPRAR | MANTENER | VENDER",
  "score": <entre -1 y 1>,
  "confianza": <entre 0 y 1>,
  "noticias_analizadas": <cantidad>,
  "positivas": <cantidad>,
  "neutrales": <cantidad>,
  "negativas": <cantidad>,
  "titulares_clave": ["<titular 1>", "<titular 2>", "<titular 3>"],
  "datos_usados": "<resumen de los datos usados>",
  "justificacion": "<explicacion basada solo en las noticias reales>"
}"""


def build_agente_sentimiento(av_key: str = ""):
    llm = ChatOpenAI(
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com",
        temperature=0,
    )
    tools = [build_noticias_bvl_tool(av_key)]
    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


async def ejecutar_agente_sentimiento(input_msg: str, av_key: str = "") -> str:
    agent = build_agente_sentimiento(av_key)
    result = await agent.ainvoke({"messages": [HumanMessage(content=input_msg)]})
    return result["messages"][-1].content

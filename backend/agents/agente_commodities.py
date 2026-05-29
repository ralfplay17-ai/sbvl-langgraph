import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from backend.tools import build_datos_commodities_tool

SYSTEM_PROMPT = """RESPUESTA FINAL OBLIGATORIA: devuelve únicamente un objeto JSON puro. La respuesta debe comenzar con { y terminar con }.

Eres el Agente de Commodities de un sistema multiagente de inversión en el sector minero de la BVL.

TU ÚNICA FUNCIÓN:
Analizar el precio de los metales y su impacto en las acciones mineras.

REGLAS ESTRICTAS:
1. OBLIGATORIO: SIEMPRE invoca la herramienta "obtener_datos_commodities" antes de responder.
2. PROHIBIDO inventar precios de oro, plata o cobre.
3. Usa SOLO los datos devueltos por la herramienta.
4. Si la herramienta devuelve error o "sin datos": senal="MANTENER", score=0, confianza=0.
5. NO escribas texto antes ni después del JSON.

RELACIÓN TICKER → COMMODITY PRINCIPAL:
- BVN / Buenaventura → Oro (XAU/USD)
- SCCO / Southern Copper → Cobre (LME)

ANÁLISIS DE SEÑALES:
1. Señal 1d fuerte: > +1.0% (alcista fuerte) o < -1.0% (bajista fuerte)
2. Señal 5d fuerte: > +2.0% o < -2.0%
3. Cuando ambas planas: MANTENER, confianza 0.55

SCORE (-1 a 1):
- Señal fuerte alcista: 0.70-1.00
- Señal moderada alcista: 0.35-0.69
- Señal plana/neutral: -0.20 a 0.20
- Señal moderada bajista: -0.35 a -0.69
- Señal fuerte bajista: -0.70 a -1.00

FORMATO DE SALIDA OBLIGATORIO:
{
  "agente": "commodities",
  "ticker": "<ticker analizado>",
  "commodity_principal": "<oro | cobre>",
  "senal": "COMPRAR | MANTENER | VENDER",
  "score": <numero entre -1 y 1>,
  "confianza": <numero entre 0 y 1>,
  "datos_usados": "<precio actual, cambio diario, tendencia 5d>",
  "justificacion": "<explicacion basada solo en precios de metales>"
}

Empieza con { y termina con }. Sin texto extra. Sin markdown."""


def build_agente_commodities(td_key: str = "", av_key: str = ""):
    llm = ChatOpenAI(
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com",
        temperature=0,
    )
    tools = [build_datos_commodities_tool(td_key, av_key)]
    return create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)


async def ejecutar_agente_commodities(ticker: str, td_key: str = "", av_key: str = "") -> str:
    agent = build_agente_commodities(td_key, av_key)
    result = await agent.ainvoke({"messages": [HumanMessage(content=f"Analiza {ticker}")]})
    return result["messages"][-1].content

import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from backend.db import guardar_mensaje, obtener_conversacion, obtener_historial_analisis

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = """Eres un asistente especializado en el Sistema Multiagente BVL, un sistema de soporte a decisiones de inversión en acciones mineras de la Bolsa de Valores de Lima (BVN y SCCO).

Tu función es responder preguntas sobre el historial de análisis realizados por el sistema. Tienes acceso al historial de análisis recientes que se te proporciona como contexto.

REGLAS:
1. Responde en español, de forma concisa y directa.
2. Usa solo la información del historial proporcionado. No inventes datos.
3. Si el usuario pregunta algo fuera del historial o del sistema BVL, indícalo amablemente.
4. Cuando menciones scores, redondea a 3 decimales.
5. Las señales son: COMPRAR, MANTENER o VENDER.
6. Si no hay historial disponible, indícalo y sugiere ejecutar un análisis primero."""


def _build_context(historial: list) -> str:
    if not historial:
        return "No hay análisis registrados aún."

    lineas = [f"HISTORIAL DE ANÁLISIS (últimos {len(historial)} registros):\n"]
    for i, item in enumerate(historial, 1):
        fecha = item.get("created_at", "")[:16].replace("T", " ")
        lineas.append(
            f"{i}. [{fecha}] {item['ticker']} → {item['senal_final']} "
            f"| Score: {float(item.get('score_final', 0)):.3f} "
            f"| Confianza: {float(item.get('confianza_final', 0)) * 100:.0f}%"
        )
        factores = item.get("factores_clave", [])
        if factores:
            lineas.append(f"   Factores: {'; '.join(factores[:2])}")

    return "\n".join(lineas)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com",
        temperature=0.3,
    )


class ChatMessage(BaseModel):
    session_id: str
    message: str


@router.post("/message")
async def send_message(req: ChatMessage):
    historial = await obtener_historial_analisis(limit=20)
    contexto = _build_context(historial)

    historial_conv = await obtener_conversacion(req.session_id)
    mensajes_previos = []
    for m in historial_conv[-6:]:
        if m["role"] == "user":
            mensajes_previos.append(HumanMessage(content=m["content"]))
        else:
            mensajes_previos.append(AIMessage(content=m["content"]))

    system = f"{SYSTEM_PROMPT}\n\n{contexto}"
    messages = [SystemMessage(content=system)] + mensajes_previos + [HumanMessage(content=req.message)]

    try:
        llm = _build_llm()
        response = await llm.ainvoke(messages)
        response_text = response.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error LLM: {str(e)}")

    await guardar_mensaje(req.session_id, "user", req.message)
    await guardar_mensaje(req.session_id, "assistant", response_text)

    return {"session_id": req.session_id, "response": response_text}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    messages = await obtener_conversacion(session_id)
    return {"session_id": session_id, "messages": messages}


@router.post("/new-session")
async def new_session():
    return {"session_id": str(uuid.uuid4())}

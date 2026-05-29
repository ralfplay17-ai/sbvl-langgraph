from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

from backend.db import guardar_mensaje, obtener_conversacion

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    session_id: str
    message: str


@router.post("/message")
async def send_message(req: ChatMessage):
    await guardar_mensaje(req.session_id, "user", req.message)

    response_text = (
        "Este es un sistema de soporte de decisiones para inversiones en mineras BVL. "
        "Usa el endpoint /analysis/run para obtener un análisis completo."
    )

    await guardar_mensaje(req.session_id, "assistant", response_text)
    return {"session_id": req.session_id, "response": response_text}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    messages = await obtener_conversacion(session_id)
    return {"session_id": session_id, "messages": messages}


@router.post("/new-session")
async def new_session():
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

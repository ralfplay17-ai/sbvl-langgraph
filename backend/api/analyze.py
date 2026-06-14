import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from agents.graph import graph
from agents.state import AnalysisState
from pso.consensus import PSOConfig
from db.supabase import guardar_analisis

router = APIRouter()


class PSOConfigRequest(BaseModel):
    n_particles: int = Field(default=50, ge=10, le=200)
    iters:       int = Field(default=100, ge=50, le=500)
    c1:          float = Field(default=0.5, ge=0.1, le=2.5)
    c2:          float = Field(default=0.3, ge=0.1, le=2.5)
    w:           float = Field(default=0.9, ge=0.1, le=1.5)


class AnalyzeRequest(BaseModel):
    ticker:     str
    pso_config: PSOConfigRequest = PSOConfigRequest()


@router.post("/analyze")
async def analyze_sse(request: AnalyzeRequest):
    """
    Ejecuta el análisis multi-agente y devuelve eventos SSE en tiempo real.
    Eventos: agent_start | agent_complete | pso_complete | final | error
    """
    pso_cfg = PSOConfig(
        n_particles=request.pso_config.n_particles,
        iters=request.pso_config.iters,
        c1=request.pso_config.c1,
        c2=request.pso_config.c2,
        w=request.pso_config.w,
    )

    initial_state: AnalysisState = {
        "ticker":          request.ticker,
        "pso_config":      pso_cfg,
        "tecnico":         None,
        "commodities":     None,
        "sentimiento":     None,
        "riesgo":          None,
        "pso_result":      None,
        "resultado_final": None,
        "events":          [],
    }

    queue: asyncio.Queue = asyncio.Queue()

    async def _run_graph():
        try:
            async for chunk in graph.astream(initial_state, stream_mode="updates"):
                for node_name, node_output in chunk.items():
                    for event in node_output.get("events", []):
                        await queue.put(event)
            await queue.put({"type": "done"})
        except Exception as e:
            await queue.put({"type": "error", "message": str(e)})
            await queue.put({"type": "done"})

    asyncio.create_task(_run_graph())

    async def event_stream():
        yield "data: " + json.dumps({"type": "start", "ticker": request.ticker}) + "\n\n"
        while True:
            event = await queue.get()
            if event["type"] == "done":
                break
            yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
            if event["type"] == "final":
                # Guardar en Supabase de forma no bloqueante
                asyncio.create_task(guardar_analisis(event["result"]))

        yield "data: " + json.dumps({"type": "close"}) + "\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        },
    )

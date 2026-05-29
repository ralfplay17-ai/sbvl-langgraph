from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers.analysis import router as analysis_router
from backend.api.routers.history import router as chat_router
from backend.api.routers.backtest import router as backtest_router

app = FastAPI(
    title="Sistema BVL Multiagente API",
    description="API para el sistema de soporte de decisiones de inversión en mineras BVL",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(chat_router)
app.include_router(backtest_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

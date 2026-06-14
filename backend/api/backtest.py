from fastapi import APIRouter
from pydantic import BaseModel, Field
import asyncio
from core.backtest import ejecutar_backtest

router = APIRouter()


class BacktestRequest(BaseModel):
    ticker: str
    dias:   int = Field(default=90, ge=30, le=1825)


@router.post("/backtest")
async def backtest(request: BacktestRequest):
    result = await asyncio.to_thread(ejecutar_backtest, request.ticker, request.dias)
    return result

from fastapi import APIRouter, Query
from db.supabase import obtener_historial, obtener_ultimo_analisis

router = APIRouter()


@router.get("/history")
async def get_history(
    ticker: str | None = Query(default=None),
    limit:  int        = Query(default=20, ge=1, le=100),
):
    return await obtener_historial(ticker=ticker, limit=limit)


@router.get("/history/{ticker}/last")
async def get_last(ticker: str):
    return await obtener_ultimo_analisis(ticker)

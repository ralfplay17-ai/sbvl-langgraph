import requests
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    ticker: str
    dias: int = 90


def _calcular_rsi(precios: pd.Series, periodo: int = 14) -> pd.Series:
    delta = precios.diff()
    ganancia = delta.where(delta > 0, 0).rolling(window=periodo).mean()
    perdida = -delta.where(delta < 0, 0).rolling(window=periodo).mean()
    return 100 - (100 / (1 + ganancia / perdida))


def _cargar_datos(ticker: str, dias: int):
    av_key = os.environ.get("ALPHA_VANTAGE_KEY", "")
    if not av_key:
        raise ValueError("ALPHA_VANTAGE_KEY no configurada")
    url = (
        f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
        f"&symbol={ticker}&outputsize=compact&apikey={av_key}"
    )
    response = requests.get(url, timeout=20)
    data = response.json()
    if "Time Series (Daily)" not in data:
        if "Information" in data or "Note" in data:
            raise ValueError("Límite diario de Alpha Vantage alcanzado (25 req/día en plan gratuito). Intenta mañana.")
        elif "Error Message" in data:
            raise ValueError(f"Error API: {data['Error Message']}")
        raise ValueError(f"Respuesta inesperada de Alpha Vantage: {list(data.keys())}")

    ts = data["Time Series (Daily)"]
    df = pd.DataFrame.from_dict(ts, orient="index")
    df.columns = ["Open", "High", "Low", "Close", "Volume"]
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    return df.sort_index().tail(dias)


@router.post("/run")
async def run_backtest(req: BacktestRequest):
    ticker = req.ticker.upper()
    if ticker not in ("BVN", "SCCO"):
        raise HTTPException(status_code=400, detail="Ticker debe ser BVN o SCCO")

    try:
        df = _cargar_datos(ticker, req.dias)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(df) < 20:
        raise HTTPException(status_code=400, detail="Datos insuficientes para backtesting")

    df["RSI"] = _calcular_rsi(df["Close"])
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["Signal"]
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    df["SMA50"] = df["Close"].rolling(window=50).mean()

    def generar_senal(row):
        if pd.isna(row["RSI"]) or pd.isna(row["SMA20"]) or pd.isna(row["SMA50"]):
            return "MANTENER"
        alc = baj = 0
        if row["RSI"] < 30:
            alc += 1
        elif row["RSI"] > 70:
            baj += 1
        if row["MACD_Hist"] > 0:
            alc += 1
        elif row["MACD_Hist"] < 0:
            baj += 1
        if row["SMA20"] > row["SMA50"]:
            alc += 1
        elif row["SMA20"] < row["SMA50"]:
            baj += 1
        if alc > baj:
            return "COMPRAR"
        elif baj > alc:
            return "VENDER"
        return "MANTENER"

    df["Senal"] = df.apply(generar_senal, axis=1)

    posicion = 0
    capital_inicial = 10000
    capital = capital_inicial
    operaciones = []
    historial_capital = []

    for i in range(len(df)):
        row = df.iloc[i]
        precio = row["Close"]
        senal = row["Senal"]
        fecha = df.index[i]

        if senal == "COMPRAR" and posicion == 0:
            posicion = capital / precio
            capital = 0
            operaciones.append({"fecha": fecha.strftime("%Y-%m-%d"), "tipo": "COMPRA", "precio": float(precio)})
        elif senal == "VENDER" and posicion > 0:
            capital = posicion * precio
            operaciones.append({
                "fecha": fecha.strftime("%Y-%m-%d"),
                "tipo": "VENTA",
                "precio": float(precio),
                "ganancia": float(capital - capital_inicial),
            })
            posicion = 0

        capital_actual = posicion * precio if posicion > 0 else capital
        historial_capital.append({"fecha": fecha.strftime("%Y-%m-%d"), "capital": float(capital_actual)})

    if posicion > 0:
        capital = posicion * df["Close"].iloc[-1]

    capital_final_pso = historial_capital[-1]["capital"]
    retorno_total_pso = (capital_final_pso - capital_inicial) / capital_inicial * 100

    capitales = pd.Series([h["capital"] for h in historial_capital])
    retornos_diarios = capitales.pct_change().dropna()
    sharpe = (retornos_diarios.mean() / retornos_diarios.std() * (252 ** 0.5)) if retornos_diarios.std() != 0 else 0
    cummax = capitales.cummax()
    max_drawdown = ((capitales - cummax) / cummax).min() * 100

    ops_cerradas = [op for op in operaciones if "ganancia" in op]
    win_rate = (len([op for op in ops_cerradas if op["ganancia"] > 0]) / len(ops_cerradas) * 100) if ops_cerradas else 0

    precio_inicial = df["Close"].iloc[0]
    precio_final = df["Close"].iloc[-1]
    retorno_bh = (precio_final - precio_inicial) / precio_inicial * 100
    capital_final_bh = capital_inicial * (1 + retorno_bh / 100)
    historial_bh = [
        {"fecha": df.index[i].strftime("%Y-%m-%d"), "capital": float(capital_inicial * (df["Close"].iloc[i] / precio_inicial))}
        for i in range(len(df))
    ]

    return {
        "ticker": ticker,
        "periodo": {
            "inicio": df.index[0].strftime("%Y-%m-%d"),
            "fin": df.index[-1].strftime("%Y-%m-%d"),
            "dias": len(df),
        },
        "estrategia_pso": {
            "capital_inicial": capital_inicial,
            "capital_final": float(capital_final_pso),
            "retorno_total": float(retorno_total_pso),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "num_operaciones": len(ops_cerradas),
            "historial_capital": historial_capital,
        },
        "buy_hold": {
            "capital_inicial": capital_inicial,
            "capital_final": float(capital_final_bh),
            "retorno_total": float(retorno_bh),
            "historial_capital": historial_bh,
        },
        "comparacion": {
            "diferencia_retorno": float(retorno_total_pso - retorno_bh),
            "ganador": "PSO" if capital_final_pso > capital_final_bh else "Buy & Hold",
        },
        "operaciones": operaciones,
    }

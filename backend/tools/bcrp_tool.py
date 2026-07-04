import json
import requests
from langchain_core.tools import tool

BCRP_BASE = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"


def _bcrp_serie(codigo: str, periodos: int = 5) -> list[dict]:
    try:
        r = requests.get(
            f"{BCRP_BASE}/{codigo}/json/ultimos-{periodos}/",
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        periods = data.get("periods", [])
        return [{"fecha": p["name"], "valor": p["values"][0]} for p in periods if p.get("values")]
    except Exception:
        return []


def _fx_av(av_key: str) -> float | None:
    try:
        r = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "FX_DAILY", "from_symbol": "USD", "to_symbol": "PEN",
                    "outputsize": "compact", "apikey": av_key},
            timeout=15,
        )
        series = r.json().get("Time Series FX (Daily)", {})
        if not series:
            return None
        last_date = sorted(series.keys())[-1]
        return float(series[last_date]["4. close"])
    except Exception:
        return None


def _fx_twelvedata(td_key: str) -> float | None:
    try:
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={"symbol": "USD/PEN", "interval": "1day", "outputsize": 1, "apikey": td_key},
            timeout=15,
        )
        values = r.json().get("values", [])
        return float(values[0]["close"]) if values else None
    except Exception:
        return None


@tool
def obtener_datos_bcrp(ticker: str) -> str:
    """
    Obtiene indicadores macroeconómicos del BCRP: tipo de cambio USD/PEN y tasa interbancaria.
    Útil para evaluar riesgo cambiario en acciones mineras peruanas.
    Input: ticker de referencia (siempre devuelve los indicadores BCRP).
    """
    from config import get_settings
    s = get_settings()

    # TC compra/venta (PD04640PD = TC venta, PD04638PD = TC compra)
    tc_venta  = _bcrp_serie("PD04640PD", 5)
    tc_compra = _bcrp_serie("PD04638PD", 5)
    tasa_int  = _bcrp_serie("PD04809PD", 5)  # tasa interbancaria overnight

    def _ultimo(serie: list[dict]) -> float | None:
        for item in reversed(serie):
            try:
                return float(item["valor"])
            except Exception:
                pass
        return None

    tc_v = _ultimo(tc_venta)
    tc_c = _ultimo(tc_compra)
    fuente_tc = "BCRP"

    if (tc_v is None or tc_c is None):
        fx = _fx_av(s.alpha_vantage_key) if s.alpha_vantage_key else None
        fuente_tc = "Alpha Vantage"
        if fx is None:
            fx = _fx_twelvedata(s.twelvedata_key) if s.twelvedata_key else None
            fuente_tc = "Twelve Data"
        if fx is not None:
            tc_v = tc_c = fx
        else:
            fuente_tc = "Sin datos"

    # Volatilidad como spread TC venta - compra normalizado
    volatilidad = None
    if tc_v and tc_c and tc_c > 0:
        volatilidad = round(abs(tc_v - tc_c) / tc_c, 6)

    return json.dumps({
        "ticker_referencia": ticker,
        "tipo_cambio": {
            "compra": tc_c,
            "venta": tc_v,
            "spread": round(tc_v - tc_c, 4) if tc_v and tc_c and fuente_tc == "BCRP" else None,
            "volatilidad_30d": volatilidad if fuente_tc == "BCRP" else None,
            "fuente": fuente_tc,
        },
        "tasa_interbancaria": {
            "ultimo": _ultimo(tasa_int),
            "serie": tasa_int[-3:],
            "fuente": "BCRP",
        },
    }, ensure_ascii=False)

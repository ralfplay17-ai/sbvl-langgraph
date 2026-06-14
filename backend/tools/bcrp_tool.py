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


@tool
def obtener_datos_bcrp(ticker: str) -> str:
    """
    Obtiene indicadores macroeconómicos del BCRP: tipo de cambio USD/PEN y tasa interbancaria.
    Útil para evaluar riesgo cambiario en acciones mineras peruanas.
    Input: ticker de referencia (siempre devuelve los indicadores BCRP).
    """
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

    # Volatilidad como spread TC venta - compra normalizado
    volatilidad = None
    if tc_v and tc_c and tc_c > 0:
        volatilidad = round(abs(tc_v - tc_c) / tc_c, 6)

    return json.dumps({
        "ticker_referencia": ticker,
        "tipo_cambio": {
            "compra": tc_c,
            "venta": tc_v,
            "spread": round(tc_v - tc_c, 4) if tc_v and tc_c else None,
            "volatilidad_30d": volatilidad,
            "fuente": "BCRP",
        },
        "tasa_interbancaria": {
            "ultimo": _ultimo(tasa_int),
            "serie": tasa_int[-3:],
            "fuente": "BCRP",
        },
    }, ensure_ascii=False)

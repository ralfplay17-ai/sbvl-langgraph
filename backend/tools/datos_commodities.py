import requests
import os
from langchain_core.tools import Tool


def build_datos_commodities_tool(td_key: str = "", av_key: str = "") -> Tool:
    _td_key = td_key or os.environ.get("TWELVE_DATA_KEY", "")
    _av_key = av_key or os.environ.get("ALPHA_VANTAGE_KEY", "")

    def obtener_datos_commodities(input_text: str = "") -> str:
        resultado = ["=== PRECIOS COMMODITIES ==="]

        # ORO: Twelve Data time series (ultimos 6 dias)
        try:
            r = requests.get(
                "https://api.twelvedata.com/time_series"
                f"?symbol=XAU/USD&interval=1day&outputsize=6&apikey={_td_key}",
                timeout=10,
            )
            d = r.json()
            values = d.get("values", [])
            if values and len(values) >= 2:
                precio_hoy = float(values[0]["close"])
                precio_ayer = float(values[1]["close"])
                cambio_diario = (precio_hoy - precio_ayer) / precio_ayer * 100
                precio_5d = float(values[min(4, len(values) - 1)]["close"])
                tendencia_5d = (precio_hoy - precio_5d) / precio_5d * 100
                dir_diaria = "sube" if cambio_diario > 0 else ("baja" if cambio_diario < 0 else "estable")
                dir_5d = "positiva" if tendencia_5d > 0 else ("negativa" if tendencia_5d < 0 else "plana")
                resultado.append(
                    f"\nOro (XAU/USD): ${precio_hoy:.2f} USD/oz"
                    f"\n  Cambio diario: {cambio_diario:+.2f}% ({dir_diaria})"
                    f"\n  Tendencia 5d:  {tendencia_5d:+.2f}% ({dir_5d})"
                )
            elif values:
                precio_hoy = float(values[0]["close"])
                resultado.append(f"\nOro (XAU/USD): ${precio_hoy:.2f} USD/oz | Cambio: N/D | Tendencia: N/D")
            else:
                resultado.append(f"\nOro: Sin datos ({d.get('message', 'error')})")
        except Exception as e:
            resultado.append(f"\nOro: Error - {e}")

        # COBRE: Alpha Vantage COPPER mensual (ultimos 3 meses)
        try:
            r2 = requests.get(
                f"https://www.alphavantage.co/query?function=COPPER&interval=monthly&apikey={_av_key}",
                timeout=10,
            )
            d2 = r2.json()
            if d2.get("Information") or d2.get("Note"):
                resultado.append(f"\nCobre: Rate limit AV ({str(d2.get('Information', d2.get('Note', '')))[:60]})")
            elif "data" in d2 and len(d2["data"]) >= 2:
                v0 = d2["data"][0]
                v1 = d2["data"][1]
                precio_ton = float(v0["value"])
                precio_lb = precio_ton / 2204.62
                precio_ton_prev = float(v1["value"])
                cambio_mes = (precio_ton - precio_ton_prev) / precio_ton_prev * 100
                dir_mes = "sube" if cambio_mes > 0 else ("baja" if cambio_mes < 0 else "estable")
                if len(d2["data"]) >= 3:
                    precio_3m = float(d2["data"][2]["value"])
                    tend_3m = (precio_ton - precio_3m) / precio_3m * 100
                    dir_3m = "positiva" if tend_3m > 0 else "negativa"
                else:
                    tend_3m, dir_3m = cambio_mes, dir_mes
                resultado.append(
                    f"\nCobre (LME): ${precio_lb:.3f} USD/lb (${precio_ton:,.0f} USD/t) - {v0['date']}"
                    f"\n  Cambio mensual: {cambio_mes:+.2f}% ({dir_mes})"
                    f"\n  Tendencia 3m:   {tend_3m:+.2f}% ({dir_3m})"
                )
            elif "data" in d2 and d2["data"]:
                v = d2["data"][0]
                precio_lb = float(v["value"]) / 2204.62
                resultado.append(f"\nCobre (LME): ${precio_lb:.3f} USD/lb - {v['date']} | Cambio: N/D")
            else:
                resultado.append("\nCobre: Sin datos")
        except Exception as e:
            resultado.append(f"\nCobre: Error - {e}")

        resultado.append("\nPlata: No disponible en plan actual (requiere Twelve Data Grow)")
        resultado.append(
            "\n\nContexto BVL:"
            "\n- BVN (Buenaventura): commodity principal = Oro"
            "\n- SCCO (Southern Copper): commodity principal = Cobre"
        )
        return "\n".join(resultado)

    return Tool(
        name="obtener_datos_commodities",
        description=(
            "Obtiene precio actual, variacion diaria y tendencia 5d/mensual de commodities: "
            "oro (XAU/USD via Twelve Data), cobre (LME via Alpha Vantage). "
            "Retorna datos para BVN (oro) y SCCO (cobre). Input: cualquier texto."
        ),
        func=obtener_datos_commodities,
    )

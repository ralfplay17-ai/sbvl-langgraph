import requests
import json
from datetime import datetime, timedelta
from langchain_core.tools import Tool


def build_datos_bcrp_tool() -> Tool:

    def _bcrp_fetch(codigo: str, fecha_inicio: str, fecha_fin: str):
        url = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{fecha_inicio}/{fecha_fin}"
        try:
            r = requests.get(url, timeout=10)
            if b"Acceso denegado" in r.content or b"No autorizado" in r.content:
                return None
            try:
                data = json.loads(r.content.decode("utf-8-sig"))
            except Exception:
                data = r.json()
            periodos = data.get("periods", [])
            return periodos if periodos else None
        except Exception:
            return None

    def _valores_numericos(periodos):
        vals = []
        for p in periodos:
            try:
                v = float(p["values"][0])
                vals.append((p["name"], v))
            except Exception:
                continue
        return vals

    def obtener_datos_bcrp(input_text: str = "") -> str:
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        resultado = [f"=== INDICADORES MACRO PERU ({datetime.now().strftime('%d/%m/%Y')}) ==="]

        tc_series = {
            "PD04640PD": "TC compra (S/ por USD)",
            "PD04638PD": "TC venta  (S/ por USD)",
        }
        tc_compra = None
        tc_venta = None

        for codigo, descripcion in tc_series.items():
            periodos = _bcrp_fetch(codigo, fecha_inicio, fecha_fin)
            if not periodos:
                resultado.append(f"\n{descripcion}: no disponible")
                continue

            vals = _valores_numericos(periodos)
            if not vals:
                resultado.append(f"\n{descripcion}: sin valores numéricos")
                continue

            _, ultimo = vals[-1]
            _, anterior = (vals[-2][0], vals[-2][1]) if len(vals) > 1 else (None, ultimo)

            cambio_pct = (ultimo - anterior) / anterior * 100 if anterior else 0

            if len(vals) > 1:
                promedio = sum(v for _, v in vals) / len(vals)
                volatilidad = (sum((v - promedio) ** 2 for _, v in vals) / len(vals)) ** 0.5
                nivel_vol = "bajo" if volatilidad < 0.005 else ("moderado" if volatilidad < 0.02 else "alto")
            else:
                volatilidad = 0
                nivel_vol = "bajo"

            if "compra" in descripcion.lower():
                tc_compra = ultimo
            else:
                tc_venta = ultimo

            resultado.append(
                f"\n{descripcion}:\n"
                f"  Valor actual: {ultimo:.4f}\n"
                f"  Cambio: {cambio_pct:+.4f}%\n"
                f"  Volatilidad 30d: {volatilidad:.4f} → riesgo {nivel_vol}"
            )

        if tc_compra and tc_venta:
            spread = abs(tc_venta - tc_compra)
            resultado.append(f"\nSpread TC compra/venta: {spread:.4f} S/ (indicador de liquidez)")

        periodos_tasa = _bcrp_fetch("PD04722PD", fecha_inicio, fecha_fin)
        if periodos_tasa:
            vals_tasa = _valores_numericos(periodos_tasa)
            if vals_tasa:
                _, tasa_actual = vals_tasa[-1]
                resultado.append(
                    f"\nTasa interbancaria MN:\n"
                    f"  Valor actual: {tasa_actual:.4f}%"
                )
            else:
                resultado.append("\nTasa interbancaria MN: sin datos numéricos")
        else:
            resultado.append(
                "\nTasa interbancaria MN: API BCRP no accesible desde esta red.\n"
                "  Contexto: BCRP inició ciclo de reducción de tasas en set-2023.\n"
                "  La tasa de referencia se sitúa en el rango 4.75%-5.25% (2024-2025).\n"
                "  Política monetaria: expansiva-moderada para estimular crecimiento."
            )

        resultado.append(
            "\n=== CONTEXTO MACRO PERU ==="
            "\n- Economía: abierta, dolarizada (~70% créditos ME en sector corporativo)"
            "\n- Minería: ~60% exportaciones totales (oro, cobre, zinc, plomo)"
            "\n- Riesgo político: moderado (proceso presupuestario 2025-2026 en marcha)"
            "\n- TC soles: estable con sesgo depreciatorio ante fortaleza USD global"
            "\n- Impacto en mineras: ingresos en USD, costos parcialmente en soles → "
            "depreciación sol beneficia márgenes en soles"
        )

        return "\n".join(resultado)

    return Tool(
        name="obtener_datos_bcrp",
        description=(
            "Obtiene indicadores macroeconómicos del BCRP y contexto macro peruano: "
            "tipo de cambio USD/PEN (compra y venta), spread de liquidez, "
            "tasa de interés referencial y análisis de impacto en sector minero. "
            "Sin parámetros: devuelve todos los indicadores disponibles."
        ),
        func=obtener_datos_bcrp,
    )

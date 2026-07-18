import sys
import os
import json
import types

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
import tools.commodities_tool as commodities_tool

obtener_datos_commodities = commodities_tool.obtener_datos_commodities.func


def _closes(values):
    return pd.Series(values, index=pd.date_range("2024-01-01", periods=len(values)))


def _settings(av_key="", td_key=""):
    return types.SimpleNamespace(alpha_vantage_key=av_key, twelvedata_key=td_key)


class TestObtenerDatosCommodities:
    def test_calcula_cambio_dia_y_tendencia_5d_correctamente(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        # Exactamente 5 puntos: iloc[-5] == iloc[0] (primer punto == "hace 5 días")
        monkeypatch.setattr(
            commodities_tool, "closes_con_fallback",
            lambda yf_sym, av_sym, td_etf, av_key, td_key: _closes([100.0, 101.0, 102.0, 103.0, 110.0]),
        )

        out = json.loads(obtener_datos_commodities("BVN"))

        oro = out["commodities"]["Oro"]
        # último=110, penúltimo=103 -> cambio_dia; hace 5 (primero)=100 -> tendencia_5d
        assert oro["precio"] == 110.0
        assert oro["cambio_dia_pct"] == round((110.0 - 103.0) / 103.0 * 100, 2)
        assert oro["tendencia_5d_pct"] == round((110.0 - 100.0) / 100.0 * 100, 2)
        assert oro["label"] == "XAU/USD"
        assert oro["unit"] == "oz"

    def test_metal_sin_datos_reporta_error_individual(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(commodities_tool, "closes_con_fallback", lambda *a: None)

        out = json.loads(obtener_datos_commodities("BVN"))

        assert out["commodities"]["Oro"] == {"error": "Sin datos"}
        assert out["commodities"]["Plata"] == {"error": "Sin datos"}
        assert out["commodities"]["Cobre"] == {"error": "Sin datos"}

    def test_serie_de_un_solo_valor_reporta_error(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(commodities_tool, "closes_con_fallback", lambda *a: _closes([100.0]))

        out = json.loads(obtener_datos_commodities("BVN"))

        assert out["commodities"]["Oro"] == {"error": "Sin datos"}

    def test_menos_de_5_puntos_usa_el_primero_como_base_de_tendencia(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(commodities_tool, "closes_con_fallback", lambda *a: _closes([100.0, 105.0, 110.0]))

        out = json.loads(obtener_datos_commodities("BVN"))

        assert out["commodities"]["Oro"]["tendencia_5d_pct"] == round((110.0 - 100.0) / 100.0 * 100, 2)

    def test_los_3_metales_se_incluyen_en_el_resultado(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(commodities_tool, "closes_con_fallback", lambda *a: _closes([100.0, 101.0]))

        out = json.loads(obtener_datos_commodities("BVN"))

        assert set(out["commodities"].keys()) == {"Oro", "Plata", "Cobre"}
        assert out["ticker_referencia"] == "BVN"

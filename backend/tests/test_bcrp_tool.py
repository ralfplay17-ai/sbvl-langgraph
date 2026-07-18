import sys
import os
import json
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
import tools.bcrp_tool as bcrp_tool

obtener_datos_bcrp = bcrp_tool.obtener_datos_bcrp.func


class FakeResponse:
    def __init__(self, data, ok=True):
        self._data = data
        self._ok = ok

    def json(self):
        return self._data

    def raise_for_status(self):
        if not self._ok:
            raise RuntimeError("HTTP error")


def _settings(av_key="", td_key=""):
    return types.SimpleNamespace(alpha_vantage_key=av_key, twelvedata_key=td_key)


# ─── _bcrp_serie ────────────────────────────────────────────────────────────

class TestBcrpSerie:
    def test_datos_validos_retorna_lista_de_periodos(self, monkeypatch):
        data = {"periods": [
            {"name": "15.Ene.24", "values": ["3.75"]},
            {"name": "16.Ene.24", "values": ["3.76"]},
        ]}
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: FakeResponse(data))

        serie = bcrp_tool._bcrp_serie("PD04640PD")

        assert serie == [{"fecha": "15.Ene.24", "valor": "3.75"}, {"fecha": "16.Ene.24", "valor": "3.76"}]

    def test_periodos_sin_values_se_omiten(self, monkeypatch):
        data = {"periods": [{"name": "15.Ene.24", "values": []}, {"name": "16.Ene.24", "values": ["3.76"]}]}
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: FakeResponse(data))
        assert bcrp_tool._bcrp_serie("PD04640PD") == [{"fecha": "16.Ene.24", "valor": "3.76"}]

    def test_error_http_retorna_lista_vacia(self, monkeypatch):
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: FakeResponse({}, ok=False))
        assert bcrp_tool._bcrp_serie("PD04640PD") == []

    def test_excepcion_de_red_retorna_lista_vacia(self, monkeypatch):
        def _raise(*a, **k):
            raise ConnectionError("WAF Incapsula challenge HTML")
        monkeypatch.setattr(bcrp_tool.requests, "get", _raise)
        assert bcrp_tool._bcrp_serie("PD04640PD") == []


# ─── _fx_av / _fx_twelvedata ────────────────────────────────────────────────

class TestFxAv:
    def test_retorna_el_cierre_mas_reciente(self, monkeypatch):
        data = {"Time Series FX (Daily)": {
            "2024-01-01": {"4. close": "3.70"},
            "2024-01-03": {"4. close": "3.72"},
            "2024-01-02": {"4. close": "3.71"},
        }}
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: FakeResponse(data))
        assert bcrp_tool._fx_av("fake-key") == 3.72

    def test_serie_vacia_retorna_none(self, monkeypatch):
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: FakeResponse({}))
        assert bcrp_tool._fx_av("fake-key") is None

    def test_excepcion_retorna_none(self, monkeypatch):
        def _raise(*a, **k):
            raise TimeoutError()
        monkeypatch.setattr(bcrp_tool.requests, "get", _raise)
        assert bcrp_tool._fx_av("fake-key") is None


class TestFxTwelvedata:
    def test_retorna_el_primer_valor(self, monkeypatch):
        data = {"values": [{"close": "3.73"}]}
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: FakeResponse(data))
        assert bcrp_tool._fx_twelvedata("fake-key") == 3.73

    def test_sin_values_retorna_none(self, monkeypatch):
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: FakeResponse({}))
        assert bcrp_tool._fx_twelvedata("fake-key") is None

    def test_excepcion_retorna_none(self, monkeypatch):
        def _raise(*a, **k):
            raise ValueError()
        monkeypatch.setattr(bcrp_tool.requests, "get", _raise)
        assert bcrp_tool._fx_twelvedata("fake-key") is None


# ─── obtener_datos_bcrp (cascada TC + tasa interbancaria) ──────────────────

class TestObtenerDatosBcrp:
    def test_bcrp_disponible_usa_bcrp_y_calcula_spread_y_volatilidad(self, monkeypatch):
        def fake_get(url, **kwargs):
            if "PD04640PD" in url:  # TC venta
                return FakeResponse({"periods": [{"name": "d", "values": ["3.80"]}]})
            if "PD04638PD" in url:  # TC compra
                return FakeResponse({"periods": [{"name": "d", "values": ["3.78"]}]})
            if "PD04809PD" in url:  # tasa interbancaria
                return FakeResponse({"periods": [{"name": "d", "values": ["5.25"]}]})
            return FakeResponse({})

        monkeypatch.setattr(bcrp_tool.requests, "get", fake_get)
        monkeypatch.setattr(config, "get_settings", lambda: _settings())

        out = obtener_datos_bcrp("BVN")

        data = json.loads(out)
        assert data["tipo_cambio"]["compra"] == 3.78
        assert data["tipo_cambio"]["venta"] == 3.80
        assert data["tipo_cambio"]["fuente"] == "BCRP"
        assert data["tipo_cambio"]["spread"] == round(3.80 - 3.78, 4)
        assert data["tipo_cambio"]["volatilidad_30d"] is not None
        assert data["tasa_interbancaria"]["ultimo"] == 5.25

    def test_bcrp_caido_fallback_a_alpha_vantage(self, monkeypatch):
        def fake_get(url, **kwargs):
            if "estadisticas.bcrp.gob.pe" in url:
                raise ConnectionError("WAF Incapsula")
            if "alphavantage.co" in url:
                return FakeResponse({"Time Series FX (Daily)": {"2024-01-01": {"4. close": "3.90"}}})
            return FakeResponse({})

        monkeypatch.setattr(bcrp_tool.requests, "get", fake_get)
        monkeypatch.setattr(config, "get_settings", lambda: _settings(av_key="av-key"))

        out = obtener_datos_bcrp("BVN")

        data = json.loads(out)
        assert data["tipo_cambio"]["fuente"] == "Alpha Vantage"
        assert data["tipo_cambio"]["compra"] == data["tipo_cambio"]["venta"] == 3.90
        # El spread/volatilidad solo se reportan cuando la fuente es BCRP
        assert data["tipo_cambio"]["spread"] is None
        assert data["tipo_cambio"]["volatilidad_30d"] is None

    def test_bcrp_y_av_caidos_fallback_a_twelvedata(self, monkeypatch):
        def fake_get(url, **kwargs):
            if "estadisticas.bcrp.gob.pe" in url:
                raise ConnectionError("WAF")
            if "alphavantage.co" in url:
                return FakeResponse({})  # sin series -> None
            if "twelvedata.com" in url:
                return FakeResponse({"values": [{"close": "3.95"}]})
            return FakeResponse({})

        monkeypatch.setattr(bcrp_tool.requests, "get", fake_get)
        monkeypatch.setattr(config, "get_settings", lambda: _settings(av_key="av-key", td_key="td-key"))

        out = obtener_datos_bcrp("BVN")

        data = json.loads(out)
        assert data["tipo_cambio"]["fuente"] == "Twelve Data"
        assert data["tipo_cambio"]["compra"] == 3.95

    def test_todo_falla_reporta_sin_datos(self, monkeypatch):
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: (_ for _ in ()).throw(ConnectionError()))
        monkeypatch.setattr(config, "get_settings", lambda: _settings())

        out = obtener_datos_bcrp("BVN")

        data = json.loads(out)
        assert data["tipo_cambio"]["fuente"] == "Sin datos"
        assert data["tipo_cambio"]["compra"] is None
        assert data["tipo_cambio"]["venta"] is None

    def test_sin_av_key_no_intenta_alpha_vantage(self, monkeypatch):
        llamados = []

        def fake_get(url, **kwargs):
            if "estadisticas.bcrp.gob.pe" in url:
                raise ConnectionError("WAF")
            if "alphavantage.co" in url:
                llamados.append("av")
            return FakeResponse({})

        monkeypatch.setattr(bcrp_tool.requests, "get", fake_get)
        monkeypatch.setattr(config, "get_settings", lambda: _settings(av_key="", td_key="td-key"))

        obtener_datos_bcrp("BVN")

        assert "av" not in llamados

    def test_ticker_referencia_se_incluye_tal_cual(self, monkeypatch):
        monkeypatch.setattr(bcrp_tool.requests, "get", lambda *a, **k: FakeResponse({}))
        monkeypatch.setattr(config, "get_settings", lambda: _settings())

        data = json.loads(obtener_datos_bcrp("SCCO"))
        assert data["ticker_referencia"] == "SCCO"

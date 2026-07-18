import sys
import os
import json

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.bvl_tool as bvl_tool

obtener_datos_bvl = bvl_tool.obtener_datos_bvl.func


def _closes(values, start="2024-01-01"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values)))


class FakeResponse:
    def __init__(self, data, ok=True):
        self._data = data
        self._ok = ok

    def json(self):
        return self._data

    def raise_for_status(self):
        if not self._ok:
            raise RuntimeError("HTTP error")


# ─── _detectar_nemonico ─────────────────────────────────────────────────────

class TestDetectarNemonico:
    def test_ticker_exacto(self):
        assert bvl_tool._detectar_nemonico("SCCO") == "SCCO"

    def test_nombre_de_empresa(self):
        assert bvl_tool._detectar_nemonico("southern copper") == "SCCO"

    def test_bvn_mapea_a_buenavc1(self):
        assert bvl_tool._detectar_nemonico("BVN") == "BUENAVC1"

    def test_texto_libre_contiene_el_ticker(self):
        assert bvl_tool._detectar_nemonico("Analiza la acción CVERDEC1 por favor") == "CVERDEC1"

    def test_no_reconocido_usa_default_buenavc1(self):
        assert bvl_tool._detectar_nemonico("XYZ123") == "BUENAVC1"

    def test_prioriza_la_clave_mas_larga(self):
        # "BROCALC1" contiene "BROCAL" como substring dentro de TICKER_MAP;
        # debe preferir la coincidencia más larga y específica, no una parcial.
        assert bvl_tool._detectar_nemonico("brocalc1") == "BROCALC1"

    def test_case_insensitive(self):
        assert bvl_tool._detectar_nemonico("scco") == "SCCO"


# ─── _f (parseo numérico defensivo) ─────────────────────────────────────────

class TestF:
    def test_valor_numerico_valido(self):
        assert bvl_tool._f("12.5") == 12.5
        assert bvl_tool._f(12.5) == 12.5

    def test_valores_centinela_retornan_none(self):
        assert bvl_tool._f(None) is None
        assert bvl_tool._f("") is None
        assert bvl_tool._f("-") is None
        assert bvl_tool._f("0") is None

    def test_valor_no_numerico_retorna_none(self):
        assert bvl_tool._f("no-es-numero") is None


# ─── _precio_rt ─────────────────────────────────────────────────────────────

class TestPrecioRt:
    def test_encuentra_el_emisor_y_extrae_precio(self, monkeypatch):
        def fake_get(url, **kwargs):
            if url.endswith("/issuers"):
                return FakeResponse([{"tkrCode": "SCCO", "companyCode": "123", "active": True}])
            if url.endswith("/issuers/123/value"):
                return FakeResponse([{"listLastValue": [
                    {"tkrCode": "SCCO", "close": "45.5", "var": "1.2", "quantityNegotiated": "1000", "coin": "USD"}
                ]}])
            return FakeResponse([])

        monkeypatch.setattr(bvl_tool.requests, "get", fake_get)
        rt = bvl_tool._precio_rt("SCCO")

        assert rt == {"precio": 45.5, "variacion_pct": 1.2, "volumen": 1000, "moneda": "USD"}

    def test_emisor_no_encontrado_retorna_none(self, monkeypatch):
        monkeypatch.setattr(bvl_tool.requests, "get", lambda url, **k: FakeResponse([]))
        assert bvl_tool._precio_rt("SCCO") is None

    def test_excepcion_de_red_retorna_none(self, monkeypatch):
        def _raise(*a, **k):
            raise ConnectionError()
        monkeypatch.setattr(bvl_tool.requests, "get", _raise)
        assert bvl_tool._precio_rt("SCCO") is None

    def test_usa_last_si_no_hay_close(self, monkeypatch):
        def fake_get(url, **kwargs):
            if url.endswith("/issuers"):
                return FakeResponse([{"tkrCode": "SCCO", "companyCode": "123", "active": True}])
            return FakeResponse([{"listLastValue": [
                {"tkrCode": "SCCO", "close": None, "last": "46.0", "var": "0", "quantityNegotiated": None}
            ]}])
        monkeypatch.setattr(bvl_tool.requests, "get", fake_get)
        rt = bvl_tool._precio_rt("SCCO")
        assert rt["precio"] == 46.0
        assert rt["volumen"] is None


# ─── _indicadores ───────────────────────────────────────────────────────────

class TestIndicadores:
    def test_usa_precio_tiempo_real_cuando_esta_disponible(self):
        close = _closes([100.0 + i for i in range(55)])
        rt = {"precio": 999.0, "variacion_pct": 2.5, "moneda": "USD"}

        out = bvl_tool._indicadores(close, "SCCO", "scco", "BVL", rt)

        assert out["precio_actual"] == 999.0
        assert out["variacion_pct"] == 2.5
        assert out["fuente_precio"] == "BVL Tiempo Real"
        assert out["moneda"] == "USD"

    def test_sin_tiempo_real_usa_ultimo_cierre_de_la_serie(self):
        close = _closes([100.0 + i for i in range(55)])

        out = bvl_tool._indicadores(close, "SCCO", "scco", "BVL", None)

        assert out["precio_actual"] == round(float(close.iloc[-1]), 4)
        assert out["fuente_precio"] == "BVL"
        assert out["moneda"] == "S/."

    def test_sma50_none_si_menos_de_50_datos(self):
        close = _closes([100.0 + i for i in range(30)])
        out = bvl_tool._indicadores(close, "SCCO", "scco", "BVL", None)
        assert out["SMA50"] is None
        assert out["tendencia"] == "indeterminada"

    def test_tendencia_alcista_cuando_sma20_mayor_a_sma50(self):
        # tendencia sostenida al alza -> SMA20 (más reciente) > SMA50
        close = _closes([100.0 + i * 2 for i in range(55)])
        out = bvl_tool._indicadores(close, "SCCO", "scco", "BVL", None)
        assert out["SMA50"] is not None
        assert out["tendencia"] == "alcista"

    def test_rsi_zona_sobrecompra_y_sobreventa(self):
        subida = _closes([50 + i for i in range(40)])  # tendencia alcista fuerte -> RSI alto
        out_alto = bvl_tool._indicadores(subida, "SCCO", "scco", "BVL", None)
        assert out_alto["RSI"] >= 70
        assert out_alto["RSI_zona"] == "sobrecompra"

        bajada = _closes([200 - i for i in range(40)])  # tendencia bajista fuerte -> RSI bajo
        out_bajo = bvl_tool._indicadores(bajada, "SCCO", "scco", "BVL", None)
        assert out_bajo["RSI"] <= 30
        assert out_bajo["RSI_zona"] == "sobreventa"

    def test_ticker_input_se_normaliza_a_mayusculas(self):
        close = _closes([100.0] * 25)
        out = bvl_tool._indicadores(close, "SCCO", "southern copper", "BVL", None)
        assert out["ticker"] == "SOUTHERN COPPER"
        assert out["nemonico_bvl"] == "SCCO"


# ─── _cargar_serie (cascada CSV -> BVL API -> Alpha Vantage) ───────────────

class TestCargarSerie:
    def test_bvl_api_devuelve_serie_valida(self, monkeypatch, tmp_path):
        monkeypatch.delenv("BVL_DATA_DIR", raising=False)
        values = [[f"2024-01-{i+1:02d}", str(10.0 + i)] for i in range(25)]
        monkeypatch.setattr(bvl_tool.requests, "get", lambda url, **k: FakeResponse({"values": values}))

        serie = bvl_tool._cargar_serie("SCCO", av_key="")

        assert serie is not None
        assert len(serie) == 25

    def test_bvl_api_con_menos_de_20_puntos_pasa_a_alpha_vantage(self, monkeypatch):
        monkeypatch.delenv("BVL_DATA_DIR", raising=False)
        llamados = []

        def fake_get(url, **kwargs):
            llamados.append(url)
            if "dataondemand.bvl.com.pe" in url:
                return FakeResponse({"values": [["2024-01-01", "10.0"]]})  # <20 puntos
            if "alphavantage.co" in url:
                ts = {f"2024-01-{i+1:02d}": {"1. open": "1", "2. high": "1", "3. low": "1",
                                              "4. close": str(10.0 + i), "5. volume": "100"} for i in range(25)}
                return FakeResponse({"Time Series (Daily)": ts})
            return FakeResponse({})

        monkeypatch.setattr(bvl_tool.requests, "get", fake_get)

        # BUENAVC1 tiene símbolo AV mapeado (BVN)
        serie = bvl_tool._cargar_serie("BUENAVC1", av_key="fake-key")

        assert serie is not None
        assert len(serie) >= 20
        assert any("alphavantage.co" in u for u in llamados)

    def test_sin_simbolo_av_mapeado_no_intenta_alpha_vantage(self, monkeypatch):
        monkeypatch.delenv("BVL_DATA_DIR", raising=False)
        llamados = []

        def fake_get(url, **kwargs):
            llamados.append(url)
            return FakeResponse({"values": []})

        monkeypatch.setattr(bvl_tool.requests, "get", fake_get)

        # CVERDEC1 no tiene ADR/símbolo en Alpha Vantage (AV_TICKER_MAP)
        serie = bvl_tool._cargar_serie("CVERDEC1", av_key="fake-key")

        assert serie is None
        assert not any("alphavantage.co" in u for u in llamados)

    def test_todo_falla_retorna_none(self, monkeypatch):
        monkeypatch.delenv("BVL_DATA_DIR", raising=False)
        monkeypatch.setattr(bvl_tool.requests, "get", lambda *a, **k: FakeResponse({}))
        assert bvl_tool._cargar_serie("SCCO", av_key="") is None

    def test_excepcion_de_red_no_rompe_la_cascada(self, monkeypatch):
        monkeypatch.delenv("BVL_DATA_DIR", raising=False)

        def _raise(*a, **k):
            raise ConnectionError()
        monkeypatch.setattr(bvl_tool.requests, "get", _raise)

        assert bvl_tool._cargar_serie("SCCO", av_key="fake-key") is None


# ─── obtener_datos_bvl (orquestación) ───────────────────────────────────────

class TestObtenerDatosBvl:
    def test_con_serie_suficiente_retorna_indicadores_completos(self, monkeypatch):
        monkeypatch.setattr(bvl_tool, "_precio_rt", lambda nemonico: None)
        monkeypatch.setattr(bvl_tool, "_cargar_serie", lambda nemonico, av_key: _closes([100.0 + i for i in range(30)]))

        out = json.loads(obtener_datos_bvl("SCCO"))

        assert out["nemonico_bvl"] == "SCCO"
        assert "RSI" in out and "MACD" in out

    def test_sin_serie_pero_con_precio_rt_retorna_solo_precio(self, monkeypatch):
        monkeypatch.setattr(bvl_tool, "_precio_rt", lambda nemonico: {"precio": 45.0, "variacion_pct": 1.0, "moneda": "USD"})
        monkeypatch.setattr(bvl_tool, "_cargar_serie", lambda nemonico, av_key: None)

        out = json.loads(obtener_datos_bvl("SCCO"))

        assert out["precio_actual"] == 45.0
        assert out["nota"] == "Sin historial suficiente para RSI/MACD/SMA"
        assert "RSI" not in out

    def test_sin_serie_y_sin_precio_retorna_error(self, monkeypatch):
        monkeypatch.setattr(bvl_tool, "_precio_rt", lambda nemonico: None)
        monkeypatch.setattr(bvl_tool, "_cargar_serie", lambda nemonico, av_key: None)

        out = json.loads(obtener_datos_bvl("XYZ"))

        assert "error" in out

    def test_serie_insuficiente_cae_a_solo_precio(self, monkeypatch):
        # menos de 20 puntos -> no alcanza para indicadores completos
        monkeypatch.setattr(bvl_tool, "_precio_rt", lambda nemonico: {"precio": 10.0, "variacion_pct": 0.0, "moneda": "S/."})
        monkeypatch.setattr(bvl_tool, "_cargar_serie", lambda nemonico, av_key: _closes([10.0] * 5))

        out = json.loads(obtener_datos_bvl("SCCO"))

        assert out["nota"] == "Sin historial suficiente para RSI/MACD/SMA"

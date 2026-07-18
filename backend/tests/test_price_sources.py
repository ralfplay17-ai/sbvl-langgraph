import sys
import os

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.price_sources as ps


def _series(values, n=None):
    n = n or len(values)
    return pd.Series(values[:n], index=pd.date_range("2024-01-01", periods=len(values[:n])))


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


# ─── closes_yf ──────────────────────────────────────────────────────────────

class TestClosesYf:
    def test_datos_validos_retorna_serie(self, monkeypatch):
        df = pd.DataFrame({"Close": [10.0, 11.0, 12.0]},
                           index=pd.date_range("2024-01-01", periods=3))
        monkeypatch.setattr(ps.yf, "download", lambda *a, **k: df)

        closes = ps.closes_yf("GC=F")
        assert closes is not None
        assert len(closes) == 3
        assert list(closes.values) == [10.0, 11.0, 12.0]

    def test_dataframe_vacio_retorna_none(self, monkeypatch):
        monkeypatch.setattr(ps.yf, "download", lambda *a, **k: pd.DataFrame())
        assert ps.closes_yf("GC=F") is None

    def test_menos_de_dos_filas_retorna_none(self, monkeypatch):
        df = pd.DataFrame({"Close": [10.0]}, index=pd.date_range("2024-01-01", periods=1))
        monkeypatch.setattr(ps.yf, "download", lambda *a, **k: df)
        assert ps.closes_yf("GC=F") is None

    def test_nan_se_descartan_y_pueden_dejar_menos_de_dos_validos(self, monkeypatch):
        df = pd.DataFrame({"Close": [10.0, None, None]},
                           index=pd.date_range("2024-01-01", periods=3))
        monkeypatch.setattr(ps.yf, "download", lambda *a, **k: df)
        assert ps.closes_yf("GC=F") is None

    def test_excepcion_de_yfinance_se_captura_y_retorna_none(self, monkeypatch):
        def _raise(*a, **k):
            raise ConnectionError("proxy 403")
        monkeypatch.setattr(ps.yf, "download", _raise)
        assert ps.closes_yf("GC=F") is None

    def test_columnas_multiindex_se_aplanan_con_squeeze(self, monkeypatch):
        # yfinance a veces devuelve columnas MultiIndex incluso para 1 ticker
        idx = pd.date_range("2024-01-01", periods=3)
        df = pd.DataFrame({("Close", "GC=F"): [10.0, 11.0, 12.0]}, index=idx)
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        monkeypatch.setattr(ps.yf, "download", lambda *a, **k: df)

        closes = ps.closes_yf("GC=F")
        assert closes is not None
        assert len(closes) == 3


# ─── closes_av_fx ───────────────────────────────────────────────────────────

class TestClosesAvFx:
    def test_datos_validos_retorna_serie_ordenada(self, monkeypatch):
        data = {
            "Time Series FX (Daily)": {
                "2024-01-03": {"4. close": "12.0"},
                "2024-01-01": {"4. close": "10.0"},
                "2024-01-02": {"4. close": "11.0"},
            }
        }
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse(data))
        closes = ps.closes_av_fx("XAU", "fake-key")
        assert closes is not None
        assert list(closes.values) == [10.0, 11.0, 12.0]

    def test_serie_vacia_retorna_none(self, monkeypatch):
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse({}))
        assert ps.closes_av_fx("XAU", "fake-key") is None

    def test_respuesta_con_nota_de_limite_retorna_none(self, monkeypatch):
        data = {"Note": "Thank you for using Alpha Vantage! Our standard API rate limit is..."}
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse(data))
        assert ps.closes_av_fx("XAU", "fake-key") is None

    def test_excepcion_de_red_se_captura_y_retorna_none(self, monkeypatch):
        def _raise(*a, **k):
            raise TimeoutError("timeout")
        monkeypatch.setattr(ps.requests, "get", _raise)
        assert ps.closes_av_fx("XAU", "fake-key") is None


# ─── closes_twelvedata ──────────────────────────────────────────────────────

class TestClosesTwelvedata:
    def test_datos_validos_se_invierten_a_orden_cronologico(self, monkeypatch):
        # Twelve Data devuelve del más reciente al más antiguo
        data = {"values": [
            {"datetime": "2024-01-03", "close": "12.0"},
            {"datetime": "2024-01-02", "close": "11.0"},
            {"datetime": "2024-01-01", "close": "10.0"},
        ]}
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse(data))
        closes = ps.closes_twelvedata("GLD", "fake-key")
        assert closes is not None
        assert list(closes.values) == [10.0, 11.0, 12.0]

    def test_sin_values_retorna_none(self, monkeypatch):
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse({}))
        assert ps.closes_twelvedata("GLD", "fake-key") is None

    def test_excepcion_se_captura_y_retorna_none(self, monkeypatch):
        def _raise(*a, **k):
            raise ValueError("json inválido")
        monkeypatch.setattr(ps.requests, "get", _raise)
        assert ps.closes_twelvedata("GLD", "fake-key") is None


# ─── closes_con_fallback (cascada) ──────────────────────────────────────────

class TestClosesConFallback:
    def test_yfinance_exitoso_no_llama_a_los_demas(self, monkeypatch):
        llamados = []
        monkeypatch.setattr(ps, "closes_yf", lambda sym: (llamados.append(("yf", sym)), _series([1.0, 2.0]))[1])
        monkeypatch.setattr(ps, "closes_av_fx", lambda *a: llamados.append("av") or None)
        monkeypatch.setattr(ps, "closes_twelvedata", lambda *a: llamados.append("td") or None)

        result = ps.closes_con_fallback("GC=F", "XAU", "GLD", "av-key", "td-key")

        assert result is not None
        assert llamados == [("yf", "GC=F")]

    def test_fallback_a_alpha_vantage_cuando_yfinance_falla(self, monkeypatch):
        llamados = []
        monkeypatch.setattr(ps, "closes_yf", lambda sym: (llamados.append(("yf", sym)), None)[1])
        monkeypatch.setattr(ps, "closes_av_fx", lambda sym, key: (llamados.append(("av", sym, key)), _series([1.0, 2.0]))[1])
        monkeypatch.setattr(ps, "closes_twelvedata", lambda *a: llamados.append("td") or None)

        result = ps.closes_con_fallback("GC=F", "XAU", "GLD", "av-key", "td-key")

        assert result is not None
        assert ("av", "XAU", "av-key") in llamados
        assert "td" not in llamados

    def test_fallback_a_twelvedata_cuando_yfinance_y_av_fallan(self, monkeypatch):
        llamados = []
        monkeypatch.setattr(ps, "closes_yf", lambda sym: (llamados.append(("yf", sym)), None)[1])
        monkeypatch.setattr(ps, "closes_av_fx", lambda *a: llamados.append("av") or None)
        monkeypatch.setattr(ps, "closes_twelvedata", lambda sym, key: (llamados.append(("td", sym, key)), _series([1.0, 2.0]))[1])

        result = ps.closes_con_fallback("GC=F", "XAU", "GLD", "av-key", "td-key")

        assert result is not None
        assert ("td", "GLD", "td-key") in llamados

    def test_ultimo_recurso_etf_via_yfinance_cuando_todo_lo_demas_falla(self, monkeypatch):
        llamados_yf = []

        def fake_yf(sym):
            llamados_yf.append(sym)
            if sym == "GLD":  # el ETF (último recurso) sí tiene datos
                return _series([1.0, 2.0])
            return None

        monkeypatch.setattr(ps, "closes_yf", fake_yf)
        monkeypatch.setattr(ps, "closes_av_fx", lambda *a: None)
        monkeypatch.setattr(ps, "closes_twelvedata", lambda *a: None)

        result = ps.closes_con_fallback("GC=F", "XAU", "GLD", "av-key", "td-key")

        assert result is not None
        assert llamados_yf == ["GC=F", "GLD"]

    def test_todas_las_fuentes_fallan_retorna_none(self, monkeypatch):
        monkeypatch.setattr(ps, "closes_yf", lambda sym: None)
        monkeypatch.setattr(ps, "closes_av_fx", lambda *a: None)
        monkeypatch.setattr(ps, "closes_twelvedata", lambda *a: None)

        assert ps.closes_con_fallback("GC=F", "XAU", "GLD", "av-key", "td-key") is None

    def test_sin_av_sym_no_llama_a_alpha_vantage(self, monkeypatch):
        # Caso real: Cobre no tiene símbolo FX en Alpha Vantage (av_sym=None)
        llamados = []
        monkeypatch.setattr(ps, "closes_yf", lambda sym: (llamados.append(("yf", sym)), None)[1] if sym == "HG=F" else _series([1.0, 2.0]))
        monkeypatch.setattr(ps, "closes_av_fx", lambda *a: llamados.append("av") or None)
        monkeypatch.setattr(ps, "closes_twelvedata", lambda sym, key: _series([1.0, 2.0]))

        ps.closes_con_fallback("HG=F", None, "COPX", "av-key", "td-key")

        assert "av" not in llamados

    def test_sin_av_key_no_llama_a_alpha_vantage(self, monkeypatch):
        llamados = []
        monkeypatch.setattr(ps, "closes_yf", lambda sym: None)
        monkeypatch.setattr(ps, "closes_av_fx", lambda *a: llamados.append("av") or None)
        monkeypatch.setattr(ps, "closes_twelvedata", lambda sym, key: _series([1.0, 2.0]))

        ps.closes_con_fallback("GC=F", "XAU", "GLD", None, "td-key")

        assert "av" not in llamados

    def test_sin_td_key_no_llama_a_twelvedata(self, monkeypatch):
        llamados = []
        monkeypatch.setattr(ps, "closes_yf", lambda sym: None)
        monkeypatch.setattr(ps, "closes_av_fx", lambda *a: None)
        monkeypatch.setattr(ps, "closes_twelvedata", lambda *a: llamados.append("td") or None)

        ps.closes_con_fallback("GC=F", "XAU", "GLD", "av-key", None)

        assert "td" not in llamados


# ─── fetch_av_news ──────────────────────────────────────────────────────────

class TestFetchAvNews:
    def test_sin_api_key_retorna_lista_vacia_sin_llamar_a_la_red(self, monkeypatch):
        llamado = []
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: llamado.append(1) or FakeResponse({}))
        assert ps.fetch_av_news("BVN", "") == []
        assert llamado == []

    def test_filtra_por_ticker_y_relevancia_minima(self, monkeypatch):
        data = {"feed": [
            {
                "title": "Buenaventura anuncia resultados",
                "time_published": "20240115T120000",
                "source": "Reuters",
                "overall_sentiment_score": 0.3,
                "overall_sentiment_label": "Somewhat-Bullish",
                "summary": "Resumen largo " * 20,
                "url": "https://example.com/1",
                "ticker_sentiment": [
                    {"ticker": "BVN", "relevance_score": "0.5"},
                ],
            },
            {
                "title": "Noticia irrelevante para BVN",
                "time_published": "20240116T120000",
                "source": "Reuters",
                "overall_sentiment_score": 0.1,
                "ticker_sentiment": [
                    {"ticker": "BVN", "relevance_score": "0.01"},  # por debajo del umbral 0.05
                ],
            },
            {
                "title": "Noticia de otro ticker",
                "time_published": "20240117T120000",
                "ticker_sentiment": [
                    {"ticker": "SCCO", "relevance_score": "0.9"},
                ],
            },
        ]}
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse(data))

        articulos = ps.fetch_av_news("BVN", "fake-key")

        assert len(articulos) == 1
        assert articulos[0]["titulo"] == "Buenaventura anuncia resultados"
        assert articulos[0]["fecha"] == "2024-01-15"
        assert articulos[0]["score"] == 0.3
        assert len(articulos[0]["resumen"]) <= 220

    def test_respuesta_con_limite_de_rate_retorna_lista_vacia(self, monkeypatch):
        data = {"Information": "Rate limit reached"}
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse(data))
        assert ps.fetch_av_news("BVN", "fake-key") == []

    def test_excepcion_se_captura_y_retorna_lista_vacia(self, monkeypatch):
        def _raise(*a, **k):
            raise ConnectionError("caído")
        monkeypatch.setattr(ps.requests, "get", _raise)
        assert ps.fetch_av_news("BVN", "fake-key") == []


# ─── fetch_google_news_rss ──────────────────────────────────────────────────

class FakeFeedEntry(dict):
    def get(self, key, default=None):
        return dict.get(self, key, default)


class FakeFeed:
    def __init__(self, entries):
        self.entries = entries


class TestFetchGoogleNewsRss:
    def test_parsea_entradas_y_limpia_html_del_resumen(self, monkeypatch):
        import feedparser
        entries = [FakeFeedEntry({
            "title": "Título de prueba",
            "published": "Mon, 15 Jan 2024 12:00:00 GMT",
            "link": "https://news.google.com/1",
            "summary": "<b>Resumen</b> con <i>html</i>",
        })]
        monkeypatch.setattr(feedparser, "parse", lambda url: FakeFeed(entries))

        articulos = ps.fetch_google_news_rss("BVN")

        assert len(articulos) == 1
        assert articulos[0]["titulo"] == "Título de prueba"
        assert articulos[0]["resumen"] == "Resumen con html"

    def test_limita_a_8_resultados(self, monkeypatch):
        import feedparser
        entries = [FakeFeedEntry({"title": f"Noticia {i}", "summary": ""}) for i in range(20)]
        monkeypatch.setattr(feedparser, "parse", lambda url: FakeFeed(entries))

        articulos = ps.fetch_google_news_rss("BVN")

        assert len(articulos) == 8

    def test_sin_entradas_retorna_lista_vacia(self, monkeypatch):
        import feedparser
        monkeypatch.setattr(feedparser, "parse", lambda url: FakeFeed([]))
        assert ps.fetch_google_news_rss("BVN") == []

    def test_excepcion_se_captura_y_retorna_lista_vacia(self, monkeypatch):
        import feedparser

        def _raise(url):
            raise RuntimeError("parse error")
        monkeypatch.setattr(feedparser, "parse", _raise)
        assert ps.fetch_google_news_rss("BVN") == []


# ─── fetch_newsapi_news ─────────────────────────────────────────────────────

class TestFetchNewsapiNews:
    def test_sin_api_key_retorna_lista_vacia_sin_llamar_a_la_red(self, monkeypatch):
        llamado = []
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: llamado.append(1) or FakeResponse({}))
        assert ps.fetch_newsapi_news("BVN", "") == []
        assert llamado == []

    def test_mapea_articulos_correctamente(self, monkeypatch):
        data = {"articles": [{
            "title": "Buenaventura sube en bolsa",
            "publishedAt": "2024-01-15T10:00:00Z",
            "url": "https://example.com/1",
            "description": "Descripción de la noticia",
            "source": {"name": "El Comercio"},
        }]}
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse(data))

        articulos = ps.fetch_newsapi_news("BVN", "fake-key")

        assert len(articulos) == 1
        assert articulos[0]["titulo"] == "Buenaventura sube en bolsa"
        assert articulos[0]["publicado"] == "2024-01-15"
        assert articulos[0]["fuente"] == "El Comercio"

    def test_descripcion_ausente_no_rompe(self, monkeypatch):
        data = {"articles": [{
            "title": "Sin descripción", "publishedAt": "2024-01-15T10:00:00Z",
            "url": "https://example.com/1", "description": None,
            "source": {"name": "El Comercio"},
        }]}
        monkeypatch.setattr(ps.requests, "get", lambda *a, **k: FakeResponse(data))
        articulos = ps.fetch_newsapi_news("BVN", "fake-key")
        assert articulos[0]["resumen"] == ""

    def test_excepcion_se_captura_y_retorna_lista_vacia(self, monkeypatch):
        def _raise(*a, **k):
            raise ConnectionError("caído")
        monkeypatch.setattr(ps.requests, "get", _raise)
        assert ps.fetch_newsapi_news("BVN", "fake-key") == []

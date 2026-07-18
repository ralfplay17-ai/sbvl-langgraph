import sys
import os
import json
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
import tools.noticias_tool as noticias_tool

obtener_noticias_bvl = noticias_tool.obtener_noticias_bvl.func


def _settings(av_key="", newsapi_key=""):
    return types.SimpleNamespace(alpha_vantage_key=av_key, newsapi_key=newsapi_key)


def _art(score=0.0):
    return {"titulo": "t", "score": score}


class TestObtenerNoticiasBvl:
    def test_calcula_tendencia_alcista(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(noticias_tool, "fetch_av_news", lambda t, k: [_art(0.3), _art(0.2), _art(-0.05)])
        monkeypatch.setattr(noticias_tool, "fetch_google_news_rss", lambda t: [{"titulo": "rss"}])

        out = json.loads(obtener_noticias_bvl("BVN"))

        assert out["resumen_sentimiento"]["alcistas"] == 2
        assert out["resumen_sentimiento"]["bajistas"] == 0
        assert out["resumen_sentimiento"]["tendencia"] == "ALCISTA"

    def test_calcula_tendencia_bajista(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(noticias_tool, "fetch_av_news", lambda t, k: [_art(-0.3), _art(-0.2)])
        monkeypatch.setattr(noticias_tool, "fetch_google_news_rss", lambda t: [])

        out = json.loads(obtener_noticias_bvl("BVN"))

        assert out["resumen_sentimiento"]["bajistas"] == 2
        assert out["resumen_sentimiento"]["tendencia"] == "BAJISTA"

    def test_tendencia_neutral_cuando_hay_empate_o_nada(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(noticias_tool, "fetch_av_news", lambda t, k: [_art(0.3), _art(-0.3)])
        monkeypatch.setattr(noticias_tool, "fetch_google_news_rss", lambda t: [])

        out = json.loads(obtener_noticias_bvl("BVN"))
        assert out["resumen_sentimiento"]["tendencia"] == "NEUTRAL"

    def test_usa_google_news_cuando_hay_resultados(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings(newsapi_key="np-key"))
        monkeypatch.setattr(noticias_tool, "fetch_av_news", lambda t, k: [])
        monkeypatch.setattr(noticias_tool, "fetch_google_news_rss", lambda t: [{"titulo": "rss1"}])
        llamado_newsapi = []
        monkeypatch.setattr(noticias_tool, "fetch_newsapi_news", lambda t, k: llamado_newsapi.append(1) or [])

        out = json.loads(obtener_noticias_bvl("BVN"))

        assert out["google_news"] == [{"titulo": "rss1"}]
        assert llamado_newsapi == []  # no debería llamarse si RSS ya tiene resultados

    def test_fallback_a_newsapi_cuando_av_y_rss_estan_vacios(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings(newsapi_key="np-key"))
        monkeypatch.setattr(noticias_tool, "fetch_av_news", lambda t, k: [])
        monkeypatch.setattr(noticias_tool, "fetch_google_news_rss", lambda t: [])
        monkeypatch.setattr(noticias_tool, "fetch_newsapi_news", lambda t, k: [{"titulo": "newsapi1"}])

        out = json.loads(obtener_noticias_bvl("BVN"))

        assert out["google_news"] == [{"titulo": "newsapi1"}]

    def test_sin_newsapi_key_no_hay_fallback(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings(newsapi_key=""))
        monkeypatch.setattr(noticias_tool, "fetch_av_news", lambda t, k: [])
        monkeypatch.setattr(noticias_tool, "fetch_google_news_rss", lambda t: [])

        out = json.loads(obtener_noticias_bvl("BVN"))

        assert out["google_news"] == []

    def test_trunca_resultados_a_10_y_5(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(noticias_tool, "fetch_av_news", lambda t, k: [_art() for _ in range(20)])
        monkeypatch.setattr(noticias_tool, "fetch_google_news_rss", lambda t: [{"titulo": f"n{i}"} for i in range(20)])

        out = json.loads(obtener_noticias_bvl("BVN"))

        assert len(out["alpha_vantage"]) == 10
        assert len(out["google_news"]) == 5

    def test_total_noticias_suma_av_mas_lo_usado_de_rss_o_newsapi(self, monkeypatch):
        monkeypatch.setattr(config, "get_settings", lambda: _settings())
        monkeypatch.setattr(noticias_tool, "fetch_av_news", lambda t, k: [_art(), _art()])
        monkeypatch.setattr(noticias_tool, "fetch_google_news_rss", lambda t: [{"titulo": "r1"}, {"titulo": "r2"}, {"titulo": "r3"}])

        out = json.loads(obtener_noticias_bvl("BVN"))

        assert out["resumen_sentimiento"]["total_noticias"] == 5

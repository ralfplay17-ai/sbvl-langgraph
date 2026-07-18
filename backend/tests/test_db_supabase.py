import sys
import os
import types
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config
import db.supabase as db


def _settings(url="", key=""):
    return types.SimpleNamespace(supabase_url=url, supabase_service_key=key)


class FakeExecResult:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    """Encadenable: .select().order().limit().eq().execute() en cualquier orden."""
    def __init__(self, table, result_data, calls):
        self._table = table
        self._result_data = result_data
        self.calls = calls

    def select(self, *a, **k):
        self.calls.append(("select", a, k))
        return self

    def insert(self, row):
        self.calls.append(("insert", row))
        return self

    def order(self, *a, **k):
        self.calls.append(("order", a, k))
        return self

    def limit(self, n):
        self.calls.append(("limit", n))
        return self

    def eq(self, field, value):
        self.calls.append(("eq", field, value))
        return self

    def execute(self):
        self.calls.append(("execute",))
        return FakeExecResult(self._result_data)


class FakeTable:
    def __init__(self, result_data, calls):
        self._result_data = result_data
        self.calls = calls

    def table(self, name):
        self.calls.append(("table", name))
        return FakeQuery(name, self._result_data, self.calls)


def _fake_client(result_data=None, calls=None):
    calls = calls if calls is not None else []
    return FakeTable(result_data, calls)


def _no_client(monkeypatch):
    monkeypatch.setattr(config, "get_settings", lambda: _settings())


def _with_client(monkeypatch, fake_client):
    monkeypatch.setattr(config, "get_settings", lambda: _settings(url="https://x.supabase.co", key="k"))
    monkeypatch.setattr(db, "_client", lambda: fake_client)


# ─── guardar_analisis ───────────────────────────────────────────────────────

class TestGuardarAnalisis:
    def test_sin_supabase_configurado_no_hace_nada(self, monkeypatch):
        _no_client(monkeypatch)
        # No debe lanzar excepción ni intentar crear un cliente real
        asyncio.run(db.guardar_analisis({"ticker": "BVN", "senal_final": "COMPRAR"}))

    def test_guarda_la_fila_con_los_campos_esperados(self, monkeypatch):
        calls = []
        fake = _fake_client(calls=calls)
        _with_client(monkeypatch, fake)

        resultado = {
            "ticker": "BVN", "senal_final": "COMPRAR", "score_final": 0.42,
            "confianza_final": 0.8, "pso_config": {"n_particles": 50},
            "detalle_agentes": {"tecnico": {"senal": "COMPRAR"}},
            "pesos_utilizados": {"tecnico": 0.5},
            "historial_convergencia": [1.0, 0.5],
        }
        asyncio.run(db.guardar_analisis(resultado))

        insert_calls = [c for c in calls if c[0] == "insert"]
        assert len(insert_calls) == 1
        row = insert_calls[0][1]
        assert row["ticker"] == "BVN"
        assert row["senal_final"] == "COMPRAR"
        assert row["score_final"] == 0.42
        assert row["pso_result"]["pesos"] == {"tecnico": 0.5}
        assert row["pso_result"]["convergencia"] == [1.0, 0.5]

    def test_senal_invalida_se_normaliza_a_mantener(self, monkeypatch):
        calls = []
        fake = _fake_client(calls=calls)
        _with_client(monkeypatch, fake)

        asyncio.run(db.guardar_analisis({"ticker": "BVN", "senal_final": "ALGO_RARO"}))

        row = next(c[1] for c in calls if c[0] == "insert")
        assert row["senal_final"] == "MANTENER"

    def test_excepcion_al_guardar_no_propaga(self, monkeypatch):
        class BrokenTable:
            def table(self, name):
                raise RuntimeError("conexión perdida")
        _with_client(monkeypatch, BrokenTable())

        # No debe lanzar -- el error se loguea y se traga
        asyncio.run(db.guardar_analisis({"ticker": "BVN", "senal_final": "COMPRAR"}))


# ─── obtener_historial ──────────────────────────────────────────────────────

class TestObtenerHistorial:
    def test_sin_supabase_configurado_retorna_lista_vacia(self, monkeypatch):
        _no_client(monkeypatch)
        assert asyncio.run(db.obtener_historial()) == []

    def test_retorna_los_datos_del_cliente(self, monkeypatch):
        fake = _fake_client(result_data=[{"ticker": "BVN"}, {"ticker": "SCCO"}])
        _with_client(monkeypatch, fake)

        result = asyncio.run(db.obtener_historial(limit=10))

        assert result == [{"ticker": "BVN"}, {"ticker": "SCCO"}]

    def test_filtra_por_ticker_cuando_se_especifica(self, monkeypatch):
        calls = []
        fake = _fake_client(result_data=[{"ticker": "BVN"}], calls=calls)
        _with_client(monkeypatch, fake)

        asyncio.run(db.obtener_historial(ticker="BVN", limit=5))

        assert ("eq", "ticker", "BVN") in calls
        assert ("limit", 5) in calls

    def test_sin_ticker_no_filtra(self, monkeypatch):
        calls = []
        fake = _fake_client(result_data=[], calls=calls)
        _with_client(monkeypatch, fake)

        asyncio.run(db.obtener_historial(ticker=None))

        assert not any(c[0] == "eq" for c in calls)

    def test_resp_data_none_retorna_lista_vacia(self, monkeypatch):
        fake = _fake_client(result_data=None)
        _with_client(monkeypatch, fake)
        assert asyncio.run(db.obtener_historial()) == []

    def test_excepcion_retorna_lista_vacia(self, monkeypatch):
        class BrokenTable:
            def table(self, name):
                raise RuntimeError("timeout")
        _with_client(monkeypatch, BrokenTable())

        assert asyncio.run(db.obtener_historial()) == []


# ─── obtener_ultimo_analisis ────────────────────────────────────────────────

class TestObtenerUltimoAnalisis:
    def test_sin_supabase_configurado_retorna_none(self, monkeypatch):
        _no_client(monkeypatch)
        assert asyncio.run(db.obtener_ultimo_analisis("BVN")) is None

    def test_retorna_el_primer_registro(self, monkeypatch):
        fake = _fake_client(result_data=[{"ticker": "BVN", "senal_final": "COMPRAR"}])
        _with_client(monkeypatch, fake)

        result = asyncio.run(db.obtener_ultimo_analisis("BVN"))
        assert result == {"ticker": "BVN", "senal_final": "COMPRAR"}

    def test_sin_registros_retorna_none(self, monkeypatch):
        fake = _fake_client(result_data=[])
        _with_client(monkeypatch, fake)
        assert asyncio.run(db.obtener_ultimo_analisis("BVN")) is None

    def test_excepcion_retorna_none(self, monkeypatch):
        class BrokenTable:
            def table(self, name):
                raise RuntimeError("timeout")
        _with_client(monkeypatch, BrokenTable())

        assert asyncio.run(db.obtener_ultimo_analisis("BVN")) is None

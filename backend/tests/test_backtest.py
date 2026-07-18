import sys
import os

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.backtest as bt


def _row(rsi=50.0, macd_h=0.0, sma20=None, sma50=None):
    return pd.Series({"RSI": rsi, "MACD_H": macd_h, "SMA20": sma20, "SMA50": sma50})


def _ohlc_df(closes, start="2024-01-01"):
    idx = pd.date_range(start, periods=len(closes))
    return pd.DataFrame({
        "Open": closes, "High": [c * 1.01 for c in closes],
        "Low": [c * 0.99 for c in closes], "Close": closes,
        "Volume": [1_000_000] * len(closes),
    }, index=idx)


# ─── _senal_row ─────────────────────────────────────────────────────────────

class TestSenalRow:
    def test_datos_insuficientes_retorna_mantener(self):
        assert bt._senal_row(_row(rsi=float("nan"), sma20=10, sma50=9)) == "MANTENER"
        assert bt._senal_row(_row(rsi=50, sma20=float("nan"), sma50=9)) == "MANTENER"
        assert bt._senal_row(_row(rsi=50, sma20=10, sma50=float("nan"))) == "MANTENER"

    def test_los_3_indicadores_alcistas_da_comprar(self):
        # RSI < 30, MACD_H > 0, SMA20 > SMA50
        senal = bt._senal_row(_row(rsi=25, macd_h=0.5, sma20=110, sma50=100))
        assert senal == "COMPRAR"

    def test_los_3_indicadores_bajistas_da_vender(self):
        senal = bt._senal_row(_row(rsi=75, macd_h=-0.5, sma20=90, sma50=100))
        assert senal == "VENDER"

    def test_dos_de_tres_alcistas_da_comprar(self):
        # RSI sobrecomprado (bajista) pero MACD y SMA alcistas -> 2 vs 1
        senal = bt._senal_row(_row(rsi=25, macd_h=0.5, sma20=110, sma50=100.0))
        assert senal == "COMPRAR"

    def test_empate_da_mantener(self):
        # RSI neutral (no suma), MACD alcista, SMA bajista -> 1 vs 1
        senal = bt._senal_row(_row(rsi=50, macd_h=0.5, sma20=90, sma50=100))
        assert senal == "MANTENER"

    def test_rsi_neutral_no_suma_a_ningun_lado(self):
        senal = bt._senal_row(_row(rsi=50, macd_h=0.0, sma20=100, sma50=100))
        assert senal == "MANTENER"


# ─── ejecutar_backtest: casos de error ──────────────────────────────────────

class TestEjecutarBacktestErrores:
    def test_sin_datos_en_ninguna_fuente_retorna_error(self, monkeypatch):
        monkeypatch.setattr(bt, "_download", lambda *a, **k: pd.DataFrame())
        monkeypatch.setattr(bt, "_download_td", lambda *a, **k: pd.DataFrame())

        result = bt.ejecutar_backtest("BVN", 90)
        assert result == {"error": "Sin datos para BVN"}

    def test_usa_twelvedata_cuando_yfinance_no_tiene_datos(self, monkeypatch):
        llamados = []
        monkeypatch.setattr(bt, "_download", lambda *a, **k: (llamados.append("yf"), pd.DataFrame())[1])
        monkeypatch.setattr(bt, "_download_td", lambda *a, **k: (llamados.append("td"), _ohlc_df([10.0] * 25))[1])
        monkeypatch.setattr(bt, "_benchmark", lambda *a: {"ticker": "N/D", "retorno_total": None, "sharpe_ratio": None})

        result = bt.ejecutar_backtest("BVN", 90)

        assert llamados == ["yf", "td"]
        assert "error" not in result

    def test_dataframe_sin_columna_close_retorna_error(self, monkeypatch):
        df = pd.DataFrame({"Open": [1, 2, 3]}, index=pd.date_range("2024-01-01", periods=3))
        monkeypatch.setattr(bt, "_download", lambda *a, **k: df)

        result = bt.ejecutar_backtest("BVN", 90)
        assert result == {"error": "Sin datos de cierre para BVN"}

    def test_menos_de_20_dias_retorna_error(self, monkeypatch):
        monkeypatch.setattr(bt, "_download", lambda *a, **k: _ohlc_df([10.0] * 10))

        result = bt.ejecutar_backtest("BVN", 90)
        assert result == {"error": "Datos insuficientes"}

    def test_excepcion_inesperada_se_captura_y_retorna_error(self, monkeypatch):
        monkeypatch.setattr(bt, "_download", lambda *a, **k: _ohlc_df([10.0 + i for i in range(25)]))

        def _raise(*a, **k):
            raise ValueError("boom")
        monkeypatch.setattr(bt, "wilder_rsi", _raise)

        result = bt.ejecutar_backtest("BVN", 90)
        assert result == {"error": "boom"}


# ─── ejecutar_backtest: simulación de estrategia (con _senal_row controlado) ─

class TestEjecutarBacktestSimulacion:
    def _correr_con_senales(self, monkeypatch, closes, senales):
        """Corre ejecutar_backtest con precios y señales por-día totalmente
        controlados (se monkeypatchea _senal_row), para poder verificar la
        lógica de simulación de cartera con aritmética exacta conocida."""
        monkeypatch.setattr(bt, "_download", lambda *a, **k: _ohlc_df(closes))
        monkeypatch.setattr(bt, "_benchmark", lambda *a: {"ticker": "N/D", "retorno_total": None, "sharpe_ratio": None})

        it = iter(senales)
        monkeypatch.setattr(bt, "_senal_row", lambda row: next(it))

        return bt.ejecutar_backtest("BVN", len(closes))

    def test_ciclo_completo_compra_y_venta_calcula_ganancia_correcta(self, monkeypatch):
        n = 25
        closes = [100.0] * n
        senales = ["MANTENER"] * n
        senales[5] = "COMPRAR"   # compra a 100
        senales[10] = "VENDER"   # vende a 100 -> ganancia 0 (mismo precio)
        closes[10] = 150.0       # sube el precio justo el día de la venta

        result = self._correr_con_senales(monkeypatch, closes, senales)

        ops = result["operaciones"]
        assert len(ops) == 2
        assert ops[0]["tipo"] == "COMPRA" and ops[0]["precio"] == 100.0
        assert ops[1]["tipo"] == "VENTA" and ops[1]["precio"] == 150.0
        # capital: 10000 / 100 = 100 acciones -> vendidas a 150 -> 15000
        assert ops[1]["ganancia"] == 5000.0
        assert result["estrategia_pso"]["num_operaciones"] == 1
        assert result["estrategia_pso"]["win_rate"] == 100.0
        assert result["estrategia_pso"]["capital_final"] == 15000.0
        assert result["estrategia_pso"]["retorno_total"] == 50.0

    def test_posicion_abierta_al_final_se_valora_a_mercado(self, monkeypatch):
        n = 25
        closes = [100.0] * n
        closes[-1] = 120.0
        senales = ["MANTENER"] * n
        senales[5] = "COMPRAR"  # nunca se vende

        result = self._correr_con_senales(monkeypatch, closes, senales)

        assert len(result["operaciones"]) == 1
        assert result["operaciones"][0]["tipo"] == "COMPRA"
        # 10000/100 = 100 acciones, valoradas al último cierre (120) = 12000
        assert result["estrategia_pso"]["capital_final"] == 12000.0
        assert result["estrategia_pso"]["num_operaciones"] == 0  # no hay operación cerrada
        assert result["estrategia_pso"]["win_rate"] == 0.0  # sin cerradas, no hay win rate

    def test_sin_operaciones_retorna_capital_inicial(self, monkeypatch):
        n = 25
        closes = [100.0] * n
        senales = ["MANTENER"] * n

        result = self._correr_con_senales(monkeypatch, closes, senales)

        assert result["operaciones"] == []
        assert result["estrategia_pso"]["capital_final"] == 10_000.0
        assert result["estrategia_pso"]["retorno_total"] == 0.0

    def test_buy_and_hold_se_calcula_independiente_de_la_estrategia(self, monkeypatch):
        n = 25
        closes = [100.0 + i for i in range(n)]  # tendencia alcista sostenida
        senales = ["MANTENER"] * n  # la estrategia PSO no opera

        result = self._correr_con_senales(monkeypatch, closes, senales)

        pi, pf = closes[0], closes[-1]
        esperado_bh = round((pf - pi) / pi * 100, 2)
        assert result["buy_hold"]["retorno_total"] == esperado_bh
        assert result["estrategia_pso"]["retorno_total"] == 0.0
        # Buy & Hold gana porque la estrategia no hizo nada y el precio subió
        assert result["comparacion"]["ganador"] == "Buy & Hold"

    def test_periodo_y_metadata_reflejan_los_dias_reales(self, monkeypatch):
        n = 25
        closes = [100.0] * n
        senales = ["MANTENER"] * n

        result = self._correr_con_senales(monkeypatch, closes, senales)

        assert result["ticker"] == "BVN"
        assert result["periodo"]["dias"] == n
        assert result["periodo"]["inicio"] == "2024-01-01"
        assert result["periodo"]["fin"] == "2024-01-25"

    def test_benchmark_se_incluye_en_el_resultado(self, monkeypatch):
        n = 25
        closes = [100.0] * n
        senales = ["MANTENER"] * n
        monkeypatch.setattr(bt, "_download", lambda *a, **k: _ohlc_df(closes))
        monkeypatch.setattr(bt, "_benchmark", lambda ini, fin: {"ticker": "EPU", "retorno_total": 3.5, "sharpe_ratio": 0.8})
        it = iter(senales)
        monkeypatch.setattr(bt, "_senal_row", lambda row: next(it))

        result = bt.ejecutar_backtest("BVN", n)

        assert result["benchmark"] == {"ticker": "EPU", "retorno_total": 3.5, "sharpe_ratio": 0.8}


# ─── _benchmark ─────────────────────────────────────────────────────────────

class TestBenchmark:
    def test_primer_simbolo_exitoso_no_prueba_el_segundo(self, monkeypatch):
        llamados = []

        def fake_download(sym, **kwargs):
            llamados.append(sym)
            return _ohlc_df([100.0 + i for i in range(25)])

        monkeypatch.setattr(bt, "_download", fake_download)
        result = bt._benchmark("2024-01-01", "2024-01-25")

        assert llamados == ["EPU"]
        assert result["ticker"] == "EPU"
        assert result["retorno_total"] is not None

    def test_fallback_al_segundo_simbolo_si_el_primero_falla(self, monkeypatch):
        def fake_download(sym, **kwargs):
            if sym == "EPU":
                return pd.DataFrame()
            return _ohlc_df([100.0 + i for i in range(25)])

        monkeypatch.setattr(bt, "_download", fake_download)
        result = bt._benchmark("2024-01-01", "2024-01-25")

        assert result["ticker"] == "^SPBLPGPT"

    def test_ambos_simbolos_fallan_retorna_nd(self, monkeypatch):
        monkeypatch.setattr(bt, "_download", lambda sym, **k: pd.DataFrame())
        result = bt._benchmark("2024-01-01", "2024-01-25")
        assert result == {"ticker": "N/D", "retorno_total": None, "sharpe_ratio": None}

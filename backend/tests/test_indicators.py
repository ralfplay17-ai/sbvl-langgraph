import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.indicators import wilder_rsi, calcular_indicadores_ohlc


def _series(values):
    return pd.Series(values, index=pd.date_range("2024-01-01", periods=len(values)))


def _ohlc_df(close_values):
    idx = pd.date_range("2024-01-01", periods=len(close_values))
    return pd.DataFrame({
        "Open":   close_values,
        "High":   [v * 1.01 for v in close_values],
        "Low":    [v * 0.99 for v in close_values],
        "Close":  close_values,
        "Volume": [1000] * len(close_values),
    }, index=idx)


class TestWilderRSI:
    def test_insufficient_data_returns_nan(self):
        rsi = wilder_rsi(_series([10.0, 11.0, 12.0]))
        assert rsi.isna().all()

    def test_rsi_range(self):
        prices = list(range(50, 110))  # tendencia alcista
        rsi = wilder_rsi(_series(prices))
        valid = rsi.dropna()
        assert len(valid) > 0
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_rsi_high_on_uptrend(self):
        prices = [float(i) for i in range(50, 110)]
        rsi = wilder_rsi(_series(prices))
        last_rsi = rsi.dropna().iloc[-1]
        assert last_rsi > 60, f"RSI={last_rsi} debería ser alto en tendencia alcista"

    def test_rsi_low_on_downtrend(self):
        prices = [float(i) for i in range(110, 50, -1)]
        rsi = wilder_rsi(_series(prices))
        last_rsi = rsi.dropna().iloc[-1]
        assert last_rsi < 40, f"RSI={last_rsi} debería ser bajo en tendencia bajista"

    def test_ignores_zero_prices(self):
        prices = [0.0, 0.0] + [float(i) for i in range(50, 110)]
        rsi = wilder_rsi(_series(prices))
        valid = rsi.dropna()
        assert len(valid) > 0


class TestCalcularIndicadoresOHLC:
    def test_returns_ohlc_fields(self):
        df = _ohlc_df([float(i) for i in range(50, 110)])
        result = calcular_indicadores_ohlc(df)
        last = result[-1]
        for key in ("fecha", "open", "high", "low", "close", "volume", "rsi", "macd", "signal", "sma20", "sma50"):
            assert key in last, f"Falta clave '{key}'"

    def test_high_gte_low(self):
        df = _ohlc_df([float(i) for i in range(50, 110)])
        result = calcular_indicadores_ohlc(df)
        for row in result:
            assert row["high"] >= row["low"]

    def test_volume_is_int(self):
        df = _ohlc_df([float(i) for i in range(50, 110)])
        result = calcular_indicadores_ohlc(df)
        for row in result:
            if row["volume"] is not None:
                assert isinstance(row["volume"], int)

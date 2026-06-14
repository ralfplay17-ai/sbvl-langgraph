"use client";

import { useState } from "react";
import BacktestChart from "@/components/charts/BacktestChart";
import { runBacktest } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { BacktestResult } from "@/lib/types";

interface Props { ticker: string }

const PERIODOS = [
  { label: "3 meses (90 días)",  dias: 90  },
  { label: "6 meses (180 días)", dias: 180 },
  { label: "1 año (365 días)",   dias: 365 },
  { label: "5 años (OE4)",       dias: 1825 },
];

function MetricCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="bg-surface-2 border border-border rounded-xl p-4 text-center">
      <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">{label}</p>
      <p className={cn("text-3xl font-black mt-1", color ?? "text-white")}>{value}</p>
      {sub && <p className="text-xs text-zinc-600 mt-0.5">{sub}</p>}
    </div>
  );
}

export default function BacktestTab({ ticker }: Props) {
  const [dias, setDias]       = useState(90);
  const [result, setResult]   = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await runBacktest(ticker, dias);
      if (r.error) setError(r.error);
      else setResult(r);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-sm font-semibold text-zinc-300">Backtesting — Validación Histórica de Estrategia</h2>
        <p className="text-xs text-zinc-600 mt-0.5">
          Compara estrategia PSO (RSI + MACD + SMA) vs Buy &amp; Hold e índice S&amp;P/BVL Peru General.
        </p>
      </div>

      {/* Controles */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex gap-2">
          {PERIODOS.map(({ label, dias: d }) => (
            <button
              key={d}
              onClick={() => setDias(d)}
              className={cn(
                "text-xs px-3 py-1.5 rounded-lg border transition-all",
                dias === d
                  ? "bg-blue-600 border-blue-500 text-white font-semibold"
                  : "border-border text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <button
          onClick={run}
          disabled={loading}
          className={cn(
            "text-sm px-5 py-2 rounded-lg font-semibold transition-all",
            loading
              ? "bg-zinc-700 text-zinc-500 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-500 text-white"
          )}
        >
          {loading ? "Ejecutando..." : "Ejecutar Backtest"}
        </button>
      </div>

      {error && (
        <div className="bg-red-950 border border-red-800 rounded-xl p-4 text-sm text-red-300">{error}</div>
      )}

      {result && !error && (
        <>
          <p className="text-xs text-zinc-500">
            <strong className="text-zinc-300">{result.ticker}</strong> ·{" "}
            {result.periodo.inicio} → {result.periodo.fin} ({result.periodo.dias} días)
          </p>

          {/* Métricas principales */}
          <div className="grid grid-cols-3 gap-4">
            <MetricCard
              label="Estrategia PSO"
              value={`${result.estrategia_pso.retorno_total >= 0 ? "+" : ""}${result.estrategia_pso.retorno_total.toFixed(2)}%`}
              sub={`Capital final: $${result.estrategia_pso.capital_final.toFixed(0)}`}
              color={result.estrategia_pso.retorno_total >= 0 ? "text-buy" : "text-sell"}
            />
            <MetricCard
              label="Buy & Hold"
              value={`${result.buy_hold.retorno_total >= 0 ? "+" : ""}${result.buy_hold.retorno_total.toFixed(2)}%`}
              sub={`Capital final: $${result.buy_hold.capital_final.toFixed(0)}`}
              color={result.buy_hold.retorno_total >= 0 ? "text-buy" : "text-sell"}
            />
            <MetricCard
              label="Ganador"
              value={result.comparacion.ganador}
              sub={`Diferencia: ${result.comparacion.diferencia >= 0 ? "+" : ""}${result.comparacion.diferencia.toFixed(2)}%`}
              color={result.comparacion.ganador === "PSO" ? "text-buy" : "text-hold"}
            />
          </div>

          {/* Gráfico */}
          <div className="bg-surface border border-border rounded-xl p-4">
            <BacktestChart data={result} />
          </div>

          {/* Riesgo */}
          <div>
            <h3 className="text-sm font-semibold text-zinc-300 mb-3">Métricas de Riesgo</h3>
            <div className="grid grid-cols-4 gap-3">
              <MetricCard
                label="Sharpe Ratio"
                value={result.estrategia_pso.sharpe_ratio.toFixed(2)}
                sub="Anualizado"
                color={result.estrategia_pso.sharpe_ratio >= 0 ? "text-buy" : "text-sell"}
              />
              <MetricCard
                label="Max Drawdown"
                value={`${result.estrategia_pso.max_drawdown.toFixed(2)}%`}
                sub="Pérdida máxima"
                color="text-sell"
              />
              <MetricCard
                label="Win Rate"
                value={`${result.estrategia_pso.win_rate.toFixed(1)}%`}
                sub={result.estrategia_pso.win_rate >= 65 ? "✓ ≥ 65% (OE4)" : "< 65% objetivo"}
                color={result.estrategia_pso.win_rate >= 65 ? "text-buy" : "text-hold"}
              />
              <MetricCard
                label="Operaciones"
                value={String(result.estrategia_pso.num_operaciones)}
                sub="Cerradas en el período"
              />
            </div>
          </div>

          {/* Benchmark */}
          {result.benchmark?.sharpe_ratio != null && (
            <div>
              <h3 className="text-sm font-semibold text-zinc-300 mb-3">
                Comparación vs Benchmark — {result.benchmark.ticker}
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <MetricCard
                  label="Sharpe PSO"
                  value={result.estrategia_pso.sharpe_ratio.toFixed(2)}
                  color={result.estrategia_pso.sharpe_ratio >= result.benchmark.sharpe_ratio ? "text-buy" : "text-sell"}
                />
                <MetricCard
                  label={`Sharpe ${result.benchmark.ticker}`}
                  value={result.benchmark.sharpe_ratio.toFixed(2)}
                />
                <MetricCard
                  label="Veredicto OE4"
                  value={result.estrategia_pso.sharpe_ratio >= result.benchmark.sharpe_ratio ? "✓ CUMPLE" : "✗ No supera"}
                  color={result.estrategia_pso.sharpe_ratio >= result.benchmark.sharpe_ratio ? "text-buy" : "text-sell"}
                />
              </div>
            </div>
          )}

          {/* Historial de operaciones */}
          {result.operaciones.length > 0 && (
            <details>
              <summary className="text-xs text-zinc-500 cursor-pointer hover:text-zinc-300 select-none">
                Historial de operaciones ({result.operaciones.length})
              </summary>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-zinc-500 border-b border-border">
                      <th className="text-left pb-2">Fecha</th>
                      <th className="text-left pb-2">Tipo</th>
                      <th className="text-right pb-2">Precio</th>
                      <th className="text-right pb-2">Ganancia</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.operaciones.map((op, i) => (
                      <tr key={i} className="border-b border-zinc-900">
                        <td className="py-1.5 text-zinc-400">{op.fecha}</td>
                        <td className={cn("py-1.5 font-semibold", op.tipo === "COMPRA" ? "text-buy" : "text-sell")}>
                          {op.tipo}
                        </td>
                        <td className="py-1.5 text-right text-zinc-300">${op.precio.toFixed(2)}</td>
                        <td className={cn("py-1.5 text-right", op.ganancia !== undefined ? (op.ganancia >= 0 ? "text-buy" : "text-sell") : "text-zinc-600")}>
                          {op.ganancia !== undefined ? `$${op.ganancia.toFixed(0)}` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </>
      )}
    </div>
  );
}

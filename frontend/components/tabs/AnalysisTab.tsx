"use client";

import { useEffect, useState } from "react";
import SignalBanner from "@/components/dashboard/SignalBanner";
import AgentCard from "@/components/dashboard/AgentCard";
import SimulatorCard from "@/components/dashboard/SimulatorCard";
import CandlestickChart from "@/components/charts/CandlestickChart";
import ConvergenceChart from "@/components/charts/ConvergenceChart";
import { getHistorico, getPrecio } from "@/lib/api";
import type { AnalysisResult, HistoricoPoint, PrecioRT, SSEEvent } from "@/lib/types";

interface Props {
  result: AnalysisResult | null;
  events: SSEEvent[];
  loading: boolean;
  ticker: string;
  capital: number;
  acciones: number;
}

const AGENTES = ["tecnico", "commodities", "sentimiento", "riesgo"];

export default function AnalysisTab({ result, events, loading, ticker, capital, acciones }: Props) {
  const [historico, setHistorico]   = useState<HistoricoPoint[]>([]);
  const [precio, setPrecio]         = useState<PrecioRT | null>(null);
  const [loadingChart, setLoadingChart] = useState(false);

  useEffect(() => {
    setLoadingChart(true);
    Promise.all([getHistorico(ticker), getPrecio(ticker)])
      .then(([h, p]) => { setHistorico(h); setPrecio(p); })
      .catch(() => {})
      .finally(() => setLoadingChart(false));
  }, [ticker]);

  // Determinar qué agentes ya completaron (por eventos SSE)
  const completedAgents = new Set(
    events.filter((e) => e.type === "agent_complete").map((e) => e.agent ?? "")
  );
  const loadingAgents = new Set(
    events.filter((e) => e.type === "agent_start").map((e) => e.agent ?? "")
  );

  if (!result && !loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4 text-center">
        <p className="text-2xl font-black text-zinc-700">Bienvenido al Dashboard BVL</p>
        <div className="flex gap-3 text-sm">
          <span className="bg-zinc-800 px-4 py-2 rounded-lg text-zinc-400">1. Selecciona empresa</span>
          <span className="bg-zinc-800 px-4 py-2 rounded-lg text-zinc-400">2. Configura PSO</span>
          <span className="bg-zinc-800 px-4 py-2 rounded-lg text-zinc-400">3. Ejecuta análisis</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Fila 1: señal + agentes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          {result ? (
            <SignalBanner data={result} precio={precio} />
          ) : (
            <div className="bg-zinc-900 border border-border rounded-2xl p-7 text-center animate-pulse h-40" />
          )}
        </div>
        <div className="lg:col-span-2 grid grid-cols-2 gap-3">
          {AGENTES.map((ag) => (
            <AgentCard
              key={ag}
              nombre={ag}
              data={result?.detalle_agentes[ag]}
              loading={loading && (loadingAgents.has(ag) || !completedAgents.has(ag))}
            />
          ))}
        </div>
      </div>

      {/* Simulador */}
      {result && (
        <SimulatorCard data={result} capital={capital} acciones={acciones} precio={precio} />
      )}

      {/* Gráfico técnico candlestick */}
      <div className="bg-surface border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold text-zinc-300 mb-3">Análisis Técnico Visual</h3>
        {loadingChart ? (
          <div className="h-64 flex items-center justify-center text-zinc-600 text-sm animate-pulse">
            Cargando datos históricos...
          </div>
        ) : (
          <CandlestickChart data={historico} ticker={ticker} />
        )}
      </div>

      {/* Fila: factores + pesos PSO */}
      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-surface border border-border rounded-xl p-4">
            <h3 className="text-sm font-semibold text-zinc-300 mb-3">Por qué esta señal</h3>
            <ul className="space-y-2">
              {result.factores_clave.map((f, i) => (
                <li key={i} className="text-xs text-zinc-400 leading-relaxed border-l-2 border-zinc-700 pl-3">
                  {f}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-surface border border-border rounded-xl p-4">
            <h3 className="text-sm font-semibold text-zinc-300 mb-3">Pesos PSO</h3>
            <div className="space-y-3">
              {Object.entries(result.pesos_utilizados).map(([nombre, peso]) => {
                const pct = Math.round(peso * 100);
                return (
                  <div key={nombre}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-zinc-400 capitalize">{nombre}</span>
                      <span className="text-zinc-200 font-mono font-semibold">{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-zinc-800 rounded overflow-hidden">
                      <div className="h-full bg-blue-500 rounded" style={{ width: `${Math.max(pct, 2)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Convergencia PSO */}
      {result?.historial_convergencia && result.historial_convergencia.length > 1 && (
        <div className="bg-surface border border-border rounded-xl p-4">
          <ConvergenceChart data={result.historial_convergencia} />
        </div>
      )}

      {/* JSON debug */}
      {result && (
        <details className="text-xs text-zinc-600">
          <summary className="cursor-pointer hover:text-zinc-400 select-none">Ver JSON completo</summary>
          <pre className="mt-2 p-3 bg-zinc-900 rounded-xl overflow-auto text-[11px] leading-relaxed">
            {JSON.stringify(result, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

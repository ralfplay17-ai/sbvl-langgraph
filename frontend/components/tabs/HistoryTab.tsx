"use client";

import { useEffect, useState, useCallback } from "react";
import { getHistory } from "@/lib/api";
import type { HistoryRecord, Senal } from "@/lib/types";
import { cn } from "@/lib/utils";
import { RefreshCw, ChevronDown, ChevronUp, History } from "lucide-react";

const AGENT_LABEL: Record<string, string> = {
  agente_tecnico:     "Técnico",
  tecnico:            "Técnico",
  agente_commodities: "Commodities",
  commodities:        "Commodities",
  agente_sentimiento: "Sentimiento",
  sentimiento:        "Sentimiento",
  agente_riesgo:      "Riesgo",
  riesgo:             "Riesgo",
};

const AGENT_ORDER = ["tecnico", "agente_tecnico", "commodities", "agente_commodities",
                     "sentimiento", "agente_sentimiento", "riesgo", "agente_riesgo"];

function senalColor(s: string) {
  if (s === "COMPRAR") return "text-buy bg-buy-bg border-green-800";
  if (s === "VENDER")  return "text-sell bg-sell-bg border-red-800";
  return "text-hold bg-hold-bg border-yellow-800";
}

function SenalBadge({ senal, tiny = false }: { senal: string; tiny?: boolean }) {
  const s = (senal || "MANTENER").toUpperCase();
  const label = tiny ? s[0] : s;
  return (
    <span className={cn(
      "font-bold border rounded leading-none",
      tiny ? "text-[9px] px-1 py-0.5" : "text-[11px] px-2 py-0.5",
      senalColor(s)
    )}>
      {label}
    </span>
  );
}

function ScoreBar({ value }: { value: number }) {
  const pct = Math.round(((value + 1) / 2) * 100);
  const color = value > 0.25 ? "bg-buy" : value < -0.25 ? "bg-sell" : "bg-hold";
  return (
    <div className="flex items-center gap-1.5">
      <div className="relative h-1 w-12 bg-zinc-800 rounded-full overflow-hidden flex-shrink-0">
        <div className={cn("absolute left-0 top-0 h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] tabular-nums text-zinc-500">
        {value >= 0 ? "+" : ""}{value.toFixed(2)}
      </span>
    </div>
  );
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "2-digit" }),
    time: d.toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" }),
  };
}

function sortedAgents(result: Record<string, { senal: string; score?: number; confianza?: number; datos_usados?: string }>) {
  const entries = Object.entries(result);
  return entries.sort(([a], [b]) => {
    const ai = AGENT_ORDER.indexOf(a);
    const bi = AGENT_ORDER.indexOf(b);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });
}

export default function HistoryTab({ isActive, refreshTrigger = 0 }: { isActive: boolean; refreshTrigger?: number }) {
  const [records,       setRecords]       = useState<HistoryRecord[]>([]);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState<string | null>(null);
  const [filterTicker,  setFilterTicker]  = useState<string | null>(null);
  const [expanded,      setExpanded]      = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getHistory(undefined, 50);
      setRecords(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (isActive) load();
  }, [isActive]);

  useEffect(() => {
    if (refreshTrigger > 0) load();
  }, [refreshTrigger]);

  const allTickers = [...new Set(records.map(r => r.ticker))].sort();
  const filtered   = filterTicker ? records.filter(r => r.ticker === filterTicker) : records;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-300">Historial de Ejecuciones</h2>
          <p className="text-xs text-zinc-600 mt-0.5">
            Cada análisis multi-agente ejecutado se guarda automáticamente.
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-border text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 transition-all disabled:opacity-40"
        >
          <RefreshCw className={cn("w-3 h-3", loading && "animate-spin")} />
          Actualizar
        </button>
      </div>

      {/* Ticker filter */}
      {allTickers.length > 1 && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setFilterTicker(null)}
            className={cn(
              "text-xs px-3 py-1 rounded-lg border transition-all",
              filterTicker === null
                ? "bg-blue-600 border-blue-500 text-white font-semibold"
                : "border-border text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
            )}
          >
            Todos ({records.length})
          </button>
          {allTickers.map(t => (
            <button
              key={t}
              onClick={() => setFilterTicker(t === filterTicker ? null : t)}
              className={cn(
                "text-xs px-3 py-1 rounded-lg border transition-all",
                filterTicker === t
                  ? "bg-blue-600 border-blue-500 text-white font-semibold"
                  : "border-border text-zinc-400 hover:border-zinc-600 hover:text-zinc-200"
              )}
            >
              {t} ({records.filter(r => r.ticker === t).length})
            </button>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-950 border border-red-800 rounded-xl p-4 text-sm text-red-300">{error}</div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && !error && (
        <div className="text-center py-20 text-zinc-600">
          <History className="w-8 h-8 mx-auto mb-3 opacity-30" />
          <p className="text-sm">Sin ejecuciones registradas todavía.</p>
          <p className="text-xs mt-1 text-zinc-700">
            Ejecutá un análisis desde el sidebar — aparecerá aquí automáticamente.
          </p>
        </div>
      )}

      {/* Table */}
      {filtered.length > 0 && (
        <div className="rounded-xl border border-border overflow-hidden">
          {/* Header row */}
          <div className="grid grid-cols-[140px_70px_110px_110px_55px_auto_28px] gap-x-4 px-4 py-2 bg-surface-2 border-b border-border">
            {["Fecha", "Ticker", "Señal Final", "Score", "Conf.", "Agentes (T·C·S·R)"].map(h => (
              <span key={h} className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">{h}</span>
            ))}
            <span />
          </div>

          {/* Data rows */}
          {filtered.map(rec => {
            const { date, time } = formatDate(rec.created_at);
            const isOpen   = expanded === rec.id;
            const agents   = sortedAgents(rec.agentes_result ?? {});
            const pesos    = Object.entries(rec.pso_result?.pesos ?? {});

            return (
              <div key={rec.id} className="border-b border-border last:border-0">
                {/* Main row — clickable */}
                <button
                  className="w-full grid grid-cols-[140px_70px_110px_110px_55px_auto_28px] gap-x-4 px-4 py-3 hover:bg-surface-2 transition-colors text-left items-center"
                  onClick={() => setExpanded(isOpen ? null : rec.id)}
                >
                  <div>
                    <p className="text-xs text-zinc-300 tabular-nums">{date}</p>
                    <p className="text-[10px] text-zinc-600 tabular-nums">{time}</p>
                  </div>

                  <span className="text-xs font-bold text-zinc-200">{rec.ticker}</span>

                  <SenalBadge senal={rec.senal_final} />

                  <ScoreBar value={rec.score_final} />

                  <span className="text-xs text-zinc-400 tabular-nums">
                    {Math.round(rec.confianza_final * 100)}%
                  </span>

                  <div className="flex gap-1">
                    {agents.map(([key, agent]) => (
                      <SenalBadge key={key} senal={agent.senal} tiny />
                    ))}
                  </div>

                  {isOpen
                    ? <ChevronUp className="w-3.5 h-3.5 text-zinc-600" />
                    : <ChevronDown className="w-3.5 h-3.5 text-zinc-600" />
                  }
                </button>

                {/* Expanded detail */}
                {isOpen && (
                  <div className="px-4 pb-5 border-t border-border bg-surface/60">
                    <div className="pt-4 grid grid-cols-2 gap-5">

                      {/* Per-agent breakdown */}
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-2.5">
                          Detalle por agente
                        </p>
                        <div className="space-y-2">
                          {agents.map(([key, agent]) => (
                            <div key={key} className="flex items-start gap-3 bg-surface-2 rounded-lg p-2.5">
                              <div className="w-24 flex-shrink-0">
                                <p className="text-[10px] font-semibold text-zinc-400 mb-1">
                                  {AGENT_LABEL[key] ?? key}
                                </p>
                                <SenalBadge senal={agent.senal} tiny />
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-3 mb-1">
                                  <span className="text-[10px] text-zinc-500">
                                    Score <span className="text-zinc-300 font-mono">
                                      {(agent.score ?? 0) >= 0 ? "+" : ""}{(agent.score ?? 0).toFixed(2)}
                                    </span>
                                  </span>
                                  <span className="text-[10px] text-zinc-500">
                                    Conf <span className="text-zinc-300 font-mono">
                                      {Math.round((agent.confianza ?? 0) * 100)}%
                                    </span>
                                  </span>
                                </div>
                                {agent.datos_usados && (
                                  <p className="text-[10px] text-zinc-600 leading-tight line-clamp-2">
                                    {agent.datos_usados}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* PSO weights */}
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-2.5">
                          Pesos PSO optimizados
                        </p>
                        {pesos.length > 0 ? (
                          <div className="space-y-2.5">
                            {pesos.map(([key, w]) => {
                              const pct = Math.round((typeof w === "number" ? w : 0) * 100);
                              return (
                                <div key={key} className="flex items-center gap-2">
                                  <span className="text-[10px] text-zinc-400 w-24 flex-shrink-0">
                                    {AGENT_LABEL[key] ?? key}
                                  </span>
                                  <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-blue-500 rounded-full transition-all"
                                      style={{ width: `${pct}%` }}
                                    />
                                  </div>
                                  <span className="text-[10px] text-zinc-500 tabular-nums w-8 text-right">
                                    {pct}%
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <p className="text-[10px] text-zinc-600">Sin datos de pesos.</p>
                        )}

                        {rec.pso_config && (
                          <div className="mt-3 pt-3 border-t border-border flex gap-3 text-[10px] text-zinc-600">
                            <span>Partículas: {rec.pso_config.n_particles}</span>
                            <span>Iter: {rec.pso_config.iters}</span>
                            <span>w={rec.pso_config.w}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

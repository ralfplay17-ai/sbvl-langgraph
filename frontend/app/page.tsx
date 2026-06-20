"use client";

import { useState, useCallback } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import Sidebar from "@/components/layout/Sidebar";
import AnalysisTab from "@/components/tabs/AnalysisTab";
import CommoditiesTab from "@/components/tabs/CommoditiesTab";
import NewsTab from "@/components/tabs/NewsTab";
import BacktestTab from "@/components/tabs/BacktestTab";
import HistoryTab from "@/components/tabs/HistoryTab";
import { streamAnalysis } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { AnalysisResult, BacktestResult, PSOConfig, SSEEvent } from "@/lib/types";

const DEFAULT_PSO: PSOConfig = {
  n_particles: 50, iters: 100, c1: 0.5, c2: 0.3, w: 0.9,
};

const TABS = [
  { value: "analisis",   label: "Análisis"    },
  { value: "commodities",label: "Commodities"  },
  { value: "noticias",   label: "Noticias"     },
  { value: "backtest",   label: "Backtesting"  },
  { value: "historial",  label: "Historial"    },
];

export default function Page() {
  const [ticker,    setTicker]    = useState("BVN");
  const [capital,   setCapital]   = useState(10_000);
  const [acciones,  setAcciones]  = useState(0);
  const [psoConfig, setPsoConfig] = useState<PSOConfig>(DEFAULT_PSO);
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState<AnalysisResult | null>(null);
  const [events,    setEvents]    = useState<SSEEvent[]>([]);
  const [activeTab, setActiveTab] = useState("analisis");

  // Estado del backtest elevado para persistir entre cambios de pestaña
  const [btResult,  setBtResult]  = useState<BacktestResult | null>(null);
  const [btLoading, setBtLoading] = useState(false);
  const [btError,   setBtError]   = useState<string | null>(null);
  const [btDias,    setBtDias]    = useState(90);

  // Trigger para refrescar historial automáticamente cuando termina un análisis
  const [histRefresh, setHistRefresh] = useState(0);

  const handleAnalyze = useCallback(() => {
    if (loading) return;
    setLoading(true);
    setResult(null);
    setEvents([]);

    const stop = streamAnalysis(
      ticker,
      psoConfig,
      (event) => {
        setEvents((prev) => [...prev, event]);
        if (event.type === "final" && event.result) {
          setResult(event.result as AnalysisResult);
          setLoading(false);
          setTimeout(() => setHistRefresh(n => n + 1), 2000);
        }
        if (event.type === "error" || event.type === "close") {
          setLoading(false);
        }
      },
      (err) => {
        console.error("SSE error:", err);
        setLoading(false);
      },
    );

    // Limpieza automática después de 5 min
    const timeout = setTimeout(() => { stop(); setLoading(false); }, 300_000);
    return () => { stop(); clearTimeout(timeout); };
  }, [ticker, psoConfig, loading]);

  return (
    <div className="flex min-h-screen">
      <Sidebar
        ticker={ticker}
        capital={capital}
        acciones={acciones}
        psoConfig={psoConfig}
        loading={loading}
        onTickerChange={(t) => { setTicker(t); setResult(null); setEvents([]); setBtResult(null); setBtError(null); }}
        onCapitalChange={setCapital}
        onAccionesChange={setAcciones}
        onPSOChange={setPsoConfig}
        onAnalyze={handleAnalyze}
      />

      <main className="flex-1 overflow-auto">
        <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
          <Tabs.List className="flex border-b border-border px-6 pt-4 gap-1 sticky top-0 bg-background z-10">
            {TABS.map(({ value, label }) => (
              <Tabs.Trigger
                key={value}
                value={value}
                className={cn(
                  "px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors select-none",
                  "data-[state=active]:text-white data-[state=active]:border-b-2 data-[state=active]:border-blue-500",
                  "data-[state=inactive]:text-zinc-500 data-[state=inactive]:hover:text-zinc-300"
                )}
              >
                {label}
              </Tabs.Trigger>
            ))}
          </Tabs.List>

          <div className="p-6">
            <Tabs.Content value="analisis" forceMount className="data-[state=inactive]:hidden">
              <AnalysisTab
                result={result}
                events={events}
                loading={loading}
                ticker={ticker}
                capital={capital}
                acciones={acciones}
              />
            </Tabs.Content>

            <Tabs.Content value="commodities" forceMount className="data-[state=inactive]:hidden">
              <CommoditiesTab />
            </Tabs.Content>

            <Tabs.Content value="noticias" forceMount className="data-[state=inactive]:hidden">
              <NewsTab ticker={ticker} />
            </Tabs.Content>

            <Tabs.Content value="backtest" forceMount className="data-[state=inactive]:hidden">
              <BacktestTab
                ticker={ticker}
                result={btResult}
                loading={btLoading}
                error={btError}
                dias={btDias}
                onDiasChange={setBtDias}
                onResult={setBtResult}
                onLoading={setBtLoading}
                onError={setBtError}
              />
            </Tabs.Content>

            <Tabs.Content value="historial" forceMount className="data-[state=inactive]:hidden">
              <HistoryTab isActive={activeTab === "historial"} refreshTrigger={histRefresh} />
            </Tabs.Content>
          </div>
        </Tabs.Root>
      </main>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { getTickers, getPrecio } from "@/lib/api";
import PSOConfigPanel from "@/components/dashboard/PSOConfig";
import type { PrecioRT, TickerOption, PSOConfig } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  ticker: string;
  capital: number;
  acciones: number;
  psoConfig: PSOConfig;
  loading: boolean;
  onTickerChange: (t: string) => void;
  onCapitalChange: (c: number) => void;
  onAccionesChange: (a: number) => void;
  onPSOChange: (cfg: PSOConfig) => void;
  onAnalyze: () => void;
}

export default function Sidebar({
  ticker, capital, acciones, psoConfig, loading,
  onTickerChange, onCapitalChange, onAccionesChange, onPSOChange, onAnalyze,
}: Props) {
  const [tickers, setTickers] = useState<TickerOption[]>([]);
  const [precio, setPrecio]   = useState<PrecioRT | null>(null);

  useEffect(() => {
    getTickers().then(setTickers).catch(() => {});
  }, []);

  useEffect(() => {
    setPrecio(null);
    getPrecio(ticker).then(setPrecio).catch(() => {});
    const interval = setInterval(() => {
      getPrecio(ticker).then(setPrecio).catch(() => {});
    }, 60_000);
    return () => clearInterval(interval);
  }, [ticker]);

  const varCls = precio?.variacion_pct && precio.variacion_pct >= 0 ? "text-buy" : "text-sell";

  return (
    <aside className="w-72 min-h-screen bg-surface border-r border-border flex flex-col p-4 gap-4 shrink-0">
      <div>
        <h1 className="text-base font-black text-white tracking-tight">Dashboard BVL</h1>
        <p className="text-xs text-zinc-500">Análisis multiagente · Sector minero</p>
      </div>

      <div className="h-px bg-border" />

      {/* Selector de empresa */}
      <div>
        <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block mb-1.5">
          Empresa / Ticker
        </label>
        <select
          value={ticker}
          onChange={(e) => onTickerChange(e.target.value)}
          className="w-full bg-zinc-900 border border-border text-zinc-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {tickers.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </div>

      {/* Precio real-time */}
      {precio && !precio.error && precio.precio && (
        <div className="bg-zinc-900 border border-border rounded-xl p-3">
          <p className="text-[10px] font-bold uppercase text-zinc-600 tracking-wider">{ticker} · Tiempo Real</p>
          <p className="text-2xl font-black text-white mt-0.5">
            {precio.moneda} {precio.precio.toFixed(2)}
          </p>
          <p className={cn("text-sm font-semibold", varCls)}>
            {(precio.variacion_pct ?? 0) >= 0 ? "▲" : "▼"} {Math.abs(precio.variacion_pct ?? 0).toFixed(2)}%
          </p>
          {precio.volumen && (
            <p className="text-[10px] text-zinc-600 mt-0.5">Vol: {precio.volumen.toLocaleString()}</p>
          )}
        </div>
      )}

      <div className="h-px bg-border" />

      {/* Capital */}
      <div>
        <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block mb-1.5">
          Capital disponible (S/.)
        </label>
        <input
          type="number"
          min={100} max={10_000_000} step={500}
          value={capital}
          onChange={(e) => onCapitalChange(Number(e.target.value))}
          className="w-full bg-zinc-900 border border-border text-zinc-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Acciones en cartera */}
      <div>
        <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block mb-1.5">
          Acciones en cartera
        </label>
        <input
          type="number"
          min={0} max={10_000_000} step={1}
          value={acciones}
          onChange={(e) => onAccionesChange(Number(e.target.value))}
          placeholder="0"
          className="w-full bg-zinc-900 border border-border text-zinc-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <p className="text-[10px] text-zinc-600 mt-1">Para simular señal de venta</p>
      </div>

      {/* PSO Config */}
      <PSOConfigPanel value={psoConfig} onChange={onPSOChange} />

      <div className="h-px bg-border" />

      {/* Botón analizar */}
      <button
        onClick={onAnalyze}
        disabled={loading}
        className={cn(
          "w-full py-3 rounded-xl text-sm font-bold uppercase tracking-wider transition-all",
          loading
            ? "bg-zinc-700 text-zinc-500 cursor-not-allowed"
            : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/30"
        )}
      >
        {loading ? "Analizando..." : "Ejecutar Análisis"}
      </button>

      <p className="text-[10px] text-zinc-600 text-center">
        Técnico · Commodities · Sentimiento · Riesgo · PSO
      </p>
    </aside>
  );
}

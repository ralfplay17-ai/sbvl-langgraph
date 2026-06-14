"use client";

import { useEffect, useState } from "react";
import SparklineChart from "@/components/charts/SparklineChart";
import { getCommodities } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { CommodityData } from "@/lib/types";

const METALS = [
  { key: "Oro",   color: "#fbbf24", rel: "BVN (Buenaventura), PODERC1 (Poderosa)" },
  { key: "Plata", color: "#94a3b8", rel: "MINSURI1 (Minsur), VOLCABC1 (Volcan), BROCALC1 (El Brocal)" },
  { key: "Cobre", color: "#f97316", rel: "SCCO (Southern Copper), CVERDEC1 (Cerro Verde), NEXAPEC1 (Nexa)" },
];

const REL_TABLE = [
  ["BVN (Buenaventura)", "Oro", "Alta"],
  ["SCCO (Southern Copper)", "Cobre", "Alta"],
  ["CVERDEC1 (Cerro Verde)", "Cobre", "Alta"],
  ["MINSURI1 (Minsur)", "Estaño/Plata", "Media"],
  ["VOLCABC1 (Volcan)", "Zinc/Plata", "Media"],
  ["BROCALC1 (El Brocal)", "Polimetálico", "Media"],
  ["NEXAPEC1 (Nexa)", "Zinc/Plata", "Media"],
];

export default function CommoditiesTab() {
  const [data, setData]       = useState<Record<string, CommodityData>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getCommodities()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-sm font-semibold text-zinc-300">Precios en Tiempo Real — Metales Industriales</h2>
        <p className="text-xs text-zinc-600 mt-0.5">Fuente: yfinance · Actualización cada 5 min</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {METALS.map(({ key, color, rel }) => {
          const d = data[key];
          return (
            <div key={key} className="bg-surface-2 border border-border rounded-xl p-5">
              {loading || !d ? (
                <div className="animate-pulse space-y-3">
                  <div className="h-3 bg-zinc-800 rounded w-16" />
                  <div className="h-7 bg-zinc-800 rounded w-32" />
                  <div className="h-2 bg-zinc-800 rounded" />
                </div>
              ) : d.error ? (
                <p className="text-red-400 text-sm">{key}: {d.error}</p>
              ) : (
                <>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-500">{key}</p>
                  <p className="text-3xl font-black text-white mt-1">${d.precio.toLocaleString()}</p>
                  <p className="text-[10px] text-zinc-500">USD/{d.unit} · {d.label}</p>
                  <div className="flex gap-3 mt-2">
                    <span className={cn("text-sm font-bold", d.cambio_dia_pct >= 0 ? "text-buy" : "text-sell")}>
                      {d.cambio_dia_pct >= 0 ? "▲" : "▼"} {Math.abs(d.cambio_dia_pct).toFixed(2)}% hoy
                    </span>
                    <span className={cn("text-xs", d.tendencia_5d_pct >= 0 ? "text-buy/70" : "text-sell/70")}>
                      {d.tendencia_5d_pct >= 0 ? "▲" : "▼"} {Math.abs(d.tendencia_5d_pct).toFixed(2)}% (5d)
                    </span>
                  </div>
                  <p className="text-[10px] text-zinc-700 mt-1">Fuente: {d.fuente}</p>
                  {d.closes?.length > 2 && (
                    <div className="mt-3">
                      <SparklineChart closes={d.closes} dates={d.dates} color={color} />
                    </div>
                  )}
                  <p className="text-[10px] text-zinc-600 mt-2">{rel}</p>
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Tabla de relevancia */}
      <div className="bg-surface border border-border rounded-xl p-4">
        <h3 className="text-sm font-semibold text-zinc-300 mb-3">Relevancia por empresa BVL</h3>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-zinc-500 border-b border-border">
              <th className="text-left pb-2 font-semibold">Empresa</th>
              <th className="text-left pb-2 font-semibold">Commodity principal</th>
              <th className="text-left pb-2 font-semibold">Correlación esperada</th>
            </tr>
          </thead>
          <tbody>
            {REL_TABLE.map(([empresa, commodity, corr]) => (
              <tr key={empresa} className="border-b border-zinc-900 hover:bg-zinc-900/40 transition-colors">
                <td className="py-2 text-zinc-300">{empresa}</td>
                <td className="py-2 text-zinc-400">{commodity}</td>
                <td className="py-2 text-zinc-500">{corr} con {commodity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

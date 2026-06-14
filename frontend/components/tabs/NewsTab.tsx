"use client";

import { useEffect, useState } from "react";
import { getNoticias } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Noticia } from "@/lib/types";

interface Props { ticker: string }

export default function NewsTab({ ticker }: Props) {
  const [av, setAv]           = useState<Noticia[]>([]);
  const [rss, setRss]         = useState<Noticia[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getNoticias(ticker)
      .then((d) => { setAv(d.alpha_vantage); setRss(d.google_news); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [ticker]);

  const alcistas = av.filter((a) => (a.score ?? 0) > 0.15).length;
  const bajistas = av.filter((a) => (a.score ?? 0) < -0.15).length;
  const tendencia = alcistas > bajistas ? "ALCISTA" : bajistas > alcistas ? "BAJISTA" : "NEUTRAL";
  const tendClr   = tendencia === "ALCISTA" ? "text-buy" : tendencia === "BAJISTA" ? "text-sell" : "text-hold";

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-sm font-semibold text-zinc-300">Noticias para <span className="text-white">{ticker}</span></h2>
        <p className="text-xs text-zinc-600 mt-0.5">Alpha Vantage NEWS_SENTIMENT · Google News RSS (español)</p>
      </div>

      {/* Resumen sentimiento */}
      {av.length > 0 && !loading && (
        <div className="grid grid-cols-4 gap-3">
          {[
            ["Analizadas", av.length, "text-zinc-300"],
            ["Alcistas", alcistas, "text-buy"],
            ["Bajistas", bajistas, "text-sell"],
            ["Tendencia", tendencia, tendClr],
          ].map(([label, val, cls]) => (
            <div key={String(label)} className="bg-surface-2 border border-border rounded-xl p-3 text-center">
              <p className="text-[10px] text-zinc-500 uppercase tracking-wider">{label}</p>
              <p className={cn("text-xl font-black mt-1", cls)}>{val}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Alpha Vantage */}
        <div>
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Alpha Vantage — Análisis financiero
          </h3>
          {loading && (
            <div className="space-y-3">
              {[1,2,3].map((i) => (
                <div key={i} className="bg-zinc-900 border border-border rounded-xl p-4 animate-pulse h-20" />
              ))}
            </div>
          )}
          {!loading && av.length === 0 && (
            <p className="text-xs text-zinc-600 bg-zinc-900 border border-border rounded-xl p-4">
              Sin noticias disponibles. Puede ser por límite de 25 req/día del plan gratuito de Alpha Vantage.
            </p>
          )}
          {!loading && av.map((art, i) => {
            const sc = art.score ?? 0;
            const bdg = sc > 0.15 ? "bg-green-950 text-green-400" : sc < -0.15 ? "bg-red-950 text-red-400" : "bg-yellow-950 text-yellow-400";
            return (
              <div key={i} className="bg-surface-2 border border-border rounded-xl p-4 mb-3">
                <div className="flex items-start gap-2 mb-1">
                  <p className="text-sm text-zinc-200 font-medium leading-snug flex-1">{art.titulo}</p>
                  <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0", bdg)}>
                    {sc > 0 ? "+" : ""}{sc.toFixed(2)}
                  </span>
                </div>
                <p className="text-[10px] text-zinc-600">{art.fecha} · {art.fuente}</p>
                <p className="text-xs text-zinc-500 mt-1.5 leading-relaxed">{art.resumen}</p>
                {art.url && (
                  <a href={art.url} target="_blank" rel="noopener noreferrer"
                    className="text-[10px] text-blue-400 hover:text-blue-300 mt-1.5 inline-block">
                    Ver artículo ↗
                  </a>
                )}
              </div>
            );
          })}
        </div>

        {/* Google News RSS */}
        <div>
          <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Google News — Noticias en español
          </h3>
          {loading && (
            <div className="space-y-3">
              {[1,2,3].map((i) => (
                <div key={i} className="bg-zinc-900 border border-border rounded-xl p-4 animate-pulse h-20" />
              ))}
            </div>
          )}
          {!loading && rss.length === 0 && (
            <p className="text-xs text-zinc-600 bg-zinc-900 border border-border rounded-xl p-4">
              Sin resultados en Google News RSS.
            </p>
          )}
          {!loading && rss.map((art, i) => (
            <div key={i} className="bg-surface-2 border border-border rounded-xl p-4 mb-3">
              <p className="text-sm text-zinc-200 font-medium leading-snug">{art.titulo}</p>
              <p className="text-[10px] text-zinc-600 mt-0.5">{art.publicado}</p>
              <p className="text-xs text-zinc-500 mt-1.5 leading-relaxed">{art.resumen}</p>
              {art.link && (
                <a href={art.link} target="_blank" rel="noopener noreferrer"
                  className="text-[10px] text-blue-400 hover:text-blue-300 mt-1.5 inline-block">
                  Leer noticia ↗
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

import { cn } from "@/lib/utils";
import type { AnalysisResult, PrecioRT } from "@/lib/types";

interface Props {
  data: AnalysisResult;
  precio?: PrecioRT | null;
}

export default function SignalBanner({ data, precio }: Props) {
  const senal = data.senal_final;
  const css = senal === "COMPRAR" ? "buy" : senal === "VENDER" ? "sell" : "hold";
  const pct = Math.round(data.confianza_final * 100);

  const colorMap = {
    buy:  { bg: "bg-buy-bg border-buy",   text: "text-buy",  label: "text-buy/80" },
    sell: { bg: "bg-sell-bg border-sell", text: "text-sell", label: "text-sell/80" },
    hold: { bg: "bg-hold-bg border-hold", text: "text-hold", label: "text-hold/80" },
  };
  const c = colorMap[css];

  return (
    <div className={cn("rounded-2xl border-2 p-7 text-center", c.bg)}>
      <p className={cn("text-xs font-bold uppercase tracking-widest mb-2", c.label)}>
        Señal Consolidada · {data.ticker}
      </p>
      <p className={cn("text-5xl font-black leading-none", c.text)}>{senal}</p>
      <p className="text-sm mt-2 text-zinc-400">
        Score PSO: <span className="text-zinc-200 font-semibold">{data.score_final.toFixed(4)}</span>
        {" · "}
        Confianza: <span className="text-zinc-200 font-semibold">{pct}%</span>
        {" · "}
        <span className="capitalize">{data.dashboard.nivel_confianza}</span>
        {typeof data.tiempo_ejecucion_s === "number" && (
          <>
            {" · "}
            {data.tiempo_ejecucion_s.toFixed(1)}s
          </>
        )}
      </p>
      {precio?.precio && (
        <p className="text-sm mt-1 text-zinc-500">
          {precio.moneda} {precio.precio.toFixed(2)}
          {" "}
          <span className={precio.variacion_pct && precio.variacion_pct >= 0 ? "text-buy" : "text-sell"}>
            {precio.variacion_pct && precio.variacion_pct >= 0 ? "▲" : "▼"}{" "}
            {Math.abs(precio.variacion_pct ?? 0).toFixed(2)}%
          </span>
        </p>
      )}
      {data.dashboard.resumen_corto && (
        <p className="text-xs text-zinc-500 mt-2 italic">{data.dashboard.resumen_corto}</p>
      )}
    </div>
  );
}

import { cn } from "@/lib/utils";
import type { AnalysisResult, PrecioRT } from "@/lib/types";

interface Props {
  data: AnalysisResult;
  capital: number;
  precio?: PrecioRT | null;
}

export default function SimulatorCard({ data, capital, precio }: Props) {
  const { senal_final, score_final, confianza_final } = data;

  if (senal_final === "MANTENER" || capital <= 0) {
    return (
      <div className="bg-hold-bg border-2 border-hold rounded-2xl p-6">
        <p className="text-xs font-bold uppercase tracking-widest text-hold/70 mb-2">Simulador de Operación</p>
        <p className="text-4xl font-black text-hold">—</p>
        <p className="text-sm text-zinc-400 mt-2">
          Señal <strong className="text-hold">MANTENER</strong> o confianza insuficiente.
          No se recomienda operar en este momento.
        </p>
      </div>
    );
  }

  const fraccion = Math.min(Math.abs(score_final) * confianza_final, 0.80);
  if (fraccion < 0.05) return null;

  const monto     = Math.round(capital * fraccion);
  const pctCap    = Math.round(fraccion * 100);
  const verbo     = senal_final === "COMPRAR" ? "INVERTIR" : "VENDER";
  const css       = senal_final === "COMPRAR" ? "buy" : "sell";
  const nivel     = confianza_final >= 0.70 ? "ALTA" : confianza_final >= 0.50 ? "MEDIA" : "BAJA";
  const badgeCss  = confianza_final >= 0.70 ? "bg-green-900 text-green-400" : confianza_final >= 0.50 ? "bg-orange-950 text-orange-400" : "bg-red-950 text-red-400";

  const colorMap = {
    buy:  "bg-buy-bg border-buy text-buy",
    sell: "bg-sell-bg border-sell text-sell",
  };

  let acciones: number | null = null;
  if (precio?.precio && precio.precio > 0) {
    acciones = Math.floor(monto / precio.precio);
  }

  return (
    <div className={cn("border-2 rounded-2xl p-6", colorMap[css])}>
      <p className="text-xs font-bold uppercase tracking-widest opacity-70 mb-2">
        Simulador de Operación · {data.ticker}
      </p>
      <p className="text-4xl font-black">
        S/. {monto.toLocaleString()}
      </p>
      <p className="text-sm text-zinc-400 mt-2 leading-relaxed">
        Recomendado <strong>{verbo}</strong> — {pctCap}% del capital disponible (S/. {capital.toLocaleString()})
        {acciones !== null && acciones > 0 && (
          <span>
            {" "}≈ <strong>{acciones.toLocaleString()} acciones</strong> a{" "}
            {precio?.moneda ?? "S/."} {precio!.precio!.toFixed(2)} c/u
          </span>
        )}
      </p>
      <p className="text-xs text-zinc-500 mt-1">
        Score PSO: {score_final.toFixed(4)} · Confianza: {Math.round(confianza_final * 100)}%
      </p>
      <span className={cn("inline-block mt-3 text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full", badgeCss)}>
        Confianza {nivel}
      </span>
    </div>
  );
}

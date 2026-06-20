import { cn } from "@/lib/utils";
import type { AnalysisResult, PrecioRT } from "@/lib/types";

interface Props {
  data: AnalysisResult;
  capital: number;
  acciones: number;
  precio?: PrecioRT | null;
}

export default function SimulatorCard({ data, capital, acciones, precio }: Props) {
  const { senal_final, score_final, confianza_final } = data;

  if (senal_final === "MANTENER") {
    return (
      <div className="bg-hold-bg border-2 border-hold rounded-2xl p-6">
        <p className="text-xs font-bold uppercase tracking-widest text-hold/70 mb-2">Simulador de Operación</p>
        <p className="text-4xl font-black text-hold">—</p>
        <p className="text-sm text-zinc-400 mt-2">
          Señal <strong className="text-hold">MANTENER</strong>. No se recomienda operar en este momento.
        </p>
      </div>
    );
  }

  const fraccion = Math.min(Math.abs(score_final) * confianza_final, 0.80);
  if (fraccion < 0.05) return null;

  const nivel    = confianza_final >= 0.70 ? "ALTA" : confianza_final >= 0.50 ? "MEDIA" : "BAJA";
  const badgeCss = confianza_final >= 0.70 ? "bg-green-900 text-green-400" : confianza_final >= 0.50 ? "bg-orange-950 text-orange-400" : "bg-red-950 text-red-400";

  // ── COMPRAR: calcula sobre capital en efectivo ──────────────────────────────
  if (senal_final === "COMPRAR") {
    if (capital <= 0) return null;
    const monto          = Math.round(capital * fraccion);
    const pctCap         = Math.round(fraccion * 100);
    const accionesCompra = precio?.precio && precio.precio > 0
      ? Math.floor(monto / precio.precio)
      : null;

    return (
      <div className="bg-buy-bg border-2 border-buy text-buy rounded-2xl p-6">
        <p className="text-xs font-bold uppercase tracking-widest opacity-70 mb-2">
          Simulador de Operación · {data.ticker}
        </p>
        <p className="text-4xl font-black">S/. {monto.toLocaleString()}</p>
        <p className="text-sm text-zinc-400 mt-2 leading-relaxed">
          Recomendado <strong>INVERTIR</strong> — {pctCap}% del capital disponible (S/. {capital.toLocaleString()})
          {accionesCompra !== null && accionesCompra > 0 && (
            <span>
              {" "}≈ <strong>{accionesCompra.toLocaleString()} acciones</strong> a{" "}
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

  // ── VENDER: calcula sobre acciones en cartera ───────────────────────────────
  if (acciones <= 0) {
    return (
      <div className="bg-sell-bg border-2 border-sell rounded-2xl p-6">
        <p className="text-xs font-bold uppercase tracking-widest text-sell/70 mb-2">Simulador de Operación · {data.ticker}</p>
        <p className="text-4xl font-black text-sell">VENDER</p>
        <p className="text-sm text-zinc-400 mt-2">
          Ingresa la cantidad de <strong className="text-zinc-300">acciones en cartera</strong> en el panel izquierdo para simular cuánto vender.
        </p>
        <span className={cn("inline-block mt-3 text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full", badgeCss)}>
          Confianza {nivel}
        </span>
      </div>
    );
  }

  const accionesVender = Math.floor(acciones * fraccion);
  const pctPos         = Math.round(fraccion * 100);
  const montoRecibido  = precio?.precio && precio.precio > 0
    ? Math.round(accionesVender * precio.precio)
    : null;

  return (
    <div className="bg-sell-bg border-2 border-sell text-sell rounded-2xl p-6">
      <p className="text-xs font-bold uppercase tracking-widest opacity-70 mb-2">
        Simulador de Operación · {data.ticker}
      </p>
      <p className="text-4xl font-black">{accionesVender.toLocaleString()} acciones</p>
      <p className="text-sm text-zinc-400 mt-2 leading-relaxed">
        Recomendado <strong>VENDER</strong> — {pctPos}% de tu posición ({acciones.toLocaleString()} acciones en cartera)
        {montoRecibido !== null && montoRecibido > 0 && (
          <span>
            {" "}→ <strong>S/. {montoRecibido.toLocaleString()}</strong> estimado a{" "}
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

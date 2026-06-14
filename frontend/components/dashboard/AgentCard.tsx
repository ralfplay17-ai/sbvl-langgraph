import { cn } from "@/lib/utils";
import type { AgentResult } from "@/lib/types";

const NOMBRES: Record<string, string> = {
  tecnico: "Técnico", commodities: "Commodities",
  sentimiento: "Sentimiento", riesgo: "Riesgo",
};

interface Props {
  nombre: string;
  data?: AgentResult;
  loading?: boolean;
}

export default function AgentCard({ nombre, data, loading }: Props) {
  const senal = data?.senal ?? "—";
  const conf  = data ? Math.round(data.confianza * 100) : 0;
  const css   = senal === "COMPRAR" ? "buy" : senal === "VENDER" ? "sell" : "hold";

  const signalColor = {
    buy:  "text-buy",
    sell: "text-sell",
    hold: "text-hold",
  }[css];

  const barColor = {
    buy:  "bg-buy",
    sell: "bg-sell",
    hold: "bg-hold",
  }[css];

  return (
    <div className="bg-surface-2 border border-border rounded-xl p-4">
      <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1">
        {NOMBRES[nombre] ?? nombre}
      </p>

      {loading ? (
        <div className="animate-pulse space-y-2 mt-2">
          <div className="h-5 bg-zinc-800 rounded w-24" />
          <div className="h-1.5 bg-zinc-800 rounded" />
        </div>
      ) : (
        <>
          <p className={cn("text-lg font-black", signalColor)}>{senal}</p>
          <p className="text-xs text-zinc-600 mt-0.5">Confianza: {conf}%</p>
          <div className="mt-2 h-1.5 bg-zinc-800 rounded overflow-hidden">
            <div
              className={cn("h-full rounded", barColor)}
              style={{ width: `${Math.max(conf, 2)}%` }}
            />
          </div>
          {data?.resumen && (
            <p className="text-xs text-zinc-500 mt-2 leading-relaxed line-clamp-3 border-t border-border pt-2">
              {data.resumen}
            </p>
          )}
        </>
      )}
    </div>
  );
}

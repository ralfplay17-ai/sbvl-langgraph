import { clsx } from 'clsx'
import type { HistoryItem, Senal } from '../types'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

interface Props {
  history: HistoryItem[]
  onSelect: (item: HistoryItem) => void
}

const senalColor: Record<Senal, string> = {
  COMPRAR: 'text-buy-text bg-buy-bg',
  MANTENER: 'text-hold-text bg-hold-bg',
  VENDER: 'text-sell-text bg-sell-bg',
}

export function HistoryPanel({ history, onSelect }: Props) {
  if (history.length === 0) {
    return (
      <div className="bg-card border border-border rounded-2xl p-6">
        <h3 className="text-white font-bold text-lg mb-3">Historial de análisis</h3>
        <p className="text-muted text-sm">Sin análisis anteriores</p>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <h3 className="text-white font-bold text-lg mb-4">Historial de análisis</h3>
      <div className="space-y-2 max-h-80 overflow-y-auto">
        {history.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(item)}
            className="w-full text-left flex items-start justify-between p-3 rounded-xl hover:bg-surface transition-colors border border-transparent hover:border-border"
          >
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="text-white font-bold">{item.ticker}</span>
                <span className={clsx('text-xs font-bold px-2 py-0.5 rounded-full', senalColor[item.senal_final])}>
                  {item.senal_final}
                </span>
              </div>
            </div>
            <div className="text-right flex flex-col gap-0.5">
              <p className="text-white font-bold text-base leading-tight">
                {item.score_final.toFixed(3)}
              </p>
              <p className="text-muted text-xs leading-tight">
                {format(new Date(item.created_at), "dd MMM, HH:mm", { locale: es })}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

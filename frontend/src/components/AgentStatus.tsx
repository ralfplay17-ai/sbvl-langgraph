import type { Senal } from '../types'
import { clsx } from 'clsx'

interface Props {
  senales: Record<string, Senal>
  confianzas: Record<string, number>
  pesos: Record<string, number>
}

const badgeClass = (senal: Senal) =>
  clsx('rounded-full px-4 py-1 text-sm font-bold text-center', {
    'bg-buy-bg text-buy-text': senal === 'COMPRAR',
    'bg-hold-bg text-hold-text': senal === 'MANTENER',
    'bg-sell-bg text-sell-text': senal === 'VENDER',
  })

const AGENTS: { key: string; nombre: string }[] = [
  { key: 'tecnico', nombre: 'Agente técnico' },
  { key: 'commodities', nombre: 'Agente commodities' },
  { key: 'sentimiento', nombre: 'Agente sentimiento' },
  { key: 'riesgo', nombre: 'Agente riesgo' },
]

export function AgentStatus({ senales, confianzas, pesos }: Props) {
  return (
    <div className="bg-card border border-border rounded-2xl p-6">
      <h3 className="text-white text-lg font-bold mb-4">Estado de los agentes</h3>
      {AGENTS.map(({ key, nombre }) => {
        const senal = (senales[key] ?? 'MANTENER') as Senal
        const conf = Math.round((confianzas[key] ?? 0) * 100)
        const peso = Math.round((pesos[key] ?? 0) * 100)
        return (
          <div key={key} className="grid grid-cols-4 items-center gap-4 py-4 border-b border-border last:border-0">
            <span className="text-white font-bold text-lg">{nombre}</span>
            <span className={badgeClass(senal)}>{senal}</span>
            <div className="h-2 bg-surface rounded-full overflow-hidden">
              <div
                className="h-2 bg-[#5ca22d] rounded-full"
                style={{ width: `${Math.max(conf, 2)}%` }}
              />
            </div>
            <div className="text-right">
              <span className="text-white text-sm">{conf}%</span>
              <span className="text-muted text-xs ml-2">({peso}% peso)</span>
            </div>
          </div>
        )
      })}
      <div className="grid grid-cols-4 items-center gap-4 py-4">
        <span className="text-white font-bold text-lg">PSO Swarm</span>
        <span className="rounded-full px-4 py-1 text-sm font-bold bg-buy-bg text-buy-text text-center">calculado</span>
        <div className="h-2 bg-surface rounded-full overflow-hidden">
          <div className="h-2 bg-[#5ca22d] rounded-full w-full" />
        </div>
        <span className="text-white text-sm text-right">✓</span>
      </div>
    </div>
  )
}

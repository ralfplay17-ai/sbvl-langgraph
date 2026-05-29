import type { AnalysisResult, Senal } from '../types'
import { clsx } from 'clsx'

interface Props {
  detalle: AnalysisResult['detalle_agentes']
  scores: AnalysisResult['scores_agentes']
  confianzas: AnalysisResult['confianzas_agentes']
}

const senalColor: Record<Senal, string> = {
  COMPRAR: 'text-buy-text',
  MANTENER: 'text-hold-text',
  VENDER: 'text-sell-text',
}

const AGENTS = [
  { key: 'tecnico' as const, nombre: 'Agente técnico' },
  { key: 'commodities' as const, nombre: 'Agente commodities' },
  { key: 'sentimiento' as const, nombre: 'Agente sentimiento' },
  { key: 'riesgo' as const, nombre: 'Agente riesgo' },
]

export function AgentDetail({ detalle, scores, confianzas }: Props) {
  return (
    <div>
      <h2 className="text-white text-xl font-bold mb-4">Detalle por agente</h2>
      <div className="grid grid-cols-2 gap-4">
        {AGENTS.map(({ key, nombre }) => {
          const agent = detalle[key]
          const score = scores[key] ?? 0
          const confianza = Math.round((confianzas[key] ?? 0) * 100)
          return (
            <div key={key} className="bg-card border border-border rounded-2xl p-6">
              <p className="text-[#bfbfba] text-base font-semibold">{nombre}</p>
              <p className={clsx('text-2xl font-bold mt-2', senalColor[agent?.senal ?? 'MANTENER'])}>
                {agent?.senal ?? 'MANTENER'}
              </p>
              <p className="text-[#a9a9a4] text-sm mt-1">
                Score: {Number(score).toFixed(3)} · Confianza: {confianza}%
              </p>
              <p className="text-[#d0d0cc] text-sm mt-3 leading-relaxed">
                {agent?.resumen ?? 'Sin resumen disponible'}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

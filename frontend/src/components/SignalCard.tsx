import type { Senal } from '../types'
import { clsx } from 'clsx'

interface Props {
  senal: Senal
  score: number
  confianza: number
  resumen?: string
}

const config = {
  COMPRAR: {
    container: 'bg-buy-bg border-buy-border',
    text: 'text-buy-text',
    label: 'COMPRAR',
  },
  MANTENER: {
    container: 'bg-hold-bg border-hold-border',
    text: 'text-hold-text',
    label: 'MANTENER',
  },
  VENDER: {
    container: 'bg-sell-bg border-sell-border',
    text: 'text-sell-text',
    label: 'VENDER',
  },
}

export function SignalCard({ senal, score, confianza, resumen }: Props) {
  const cfg = config[senal]
  const pct = Math.round(confianza * 100)

  return (
    <div className={clsx('border-2 rounded-2xl p-8 text-center', cfg.container)}>
      <p className={clsx('text-lg font-bold', cfg.text)}>Señal consolidada</p>
      <p className={clsx('text-6xl font-extrabold my-3', cfg.text)}>{cfg.label}</p>
      <p className={clsx('text-xl font-semibold', cfg.text)}>
        Score: {score.toFixed(4)} &nbsp;|&nbsp; Confianza: {pct}%
      </p>
      {resumen && (
        <p className={clsx('mt-3 text-sm', cfg.text)}>{resumen}</p>
      )}
    </div>
  )
}

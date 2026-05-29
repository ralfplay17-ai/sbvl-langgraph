interface Props {
  pesos: {
    tecnico: number
    commodities: number
    sentimiento: number
    riesgo: number
  }
}

const LABELS = [
  { key: 'tecnico' as const, label: 'Técnico' },
  { key: 'commodities' as const, label: 'Commodities' },
  { key: 'sentimiento' as const, label: 'Sentimiento' },
  { key: 'riesgo' as const, label: 'Riesgo' },
]

export function PSOWeights({ pesos }: Props) {
  return (
    <div>
      <h2 className="text-white text-xl font-bold mb-4">Pesos optimizados por PSO</h2>
      <div className="grid grid-cols-4 gap-4">
        {LABELS.map(({ key, label }) => (
          <div key={key} className="bg-card border border-border rounded-2xl p-6">
            <p className="text-[#bfbfba] text-base font-semibold">{label}</p>
            <p className="text-white text-4xl font-bold mt-3">
              {Math.round(pesos[key] * 100)}%
            </p>
            <p className="text-[#a9a9a4] text-sm mt-1">peso PSO</p>
          </div>
        ))}
      </div>
    </div>
  )
}

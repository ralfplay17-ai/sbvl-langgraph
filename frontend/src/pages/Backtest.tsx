import { useState } from 'react'
import { runBacktest } from '../lib/api'
import type { BacktestResult } from '../types'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

type Ticker = 'BVN' | 'SCCO'
type Period = 90 | 180 | 365

const PERIODS: { label: string; dias: Period }[] = [
  { label: '3 meses', dias: 90 },
  { label: '6 meses', dias: 180 },
  { label: '1 año', dias: 365 },
]

export function Backtest() {
  const [ticker, setTicker] = useState<Ticker>('BVN')
  const [dias, setDias] = useState<Period>(90)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await runBacktest(ticker, dias)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  const chartData = result
    ? result.estrategia_pso.historial_capital.map((pso, i) => ({
        fecha: pso.fecha,
        PSO: pso.capital,
        BuyHold: result.buy_hold.historial_capital[i]?.capital ?? null,
      }))
    : []

  return (
    <div className="min-h-screen bg-surface p-6 space-y-6">
      <h1 className="text-white text-3xl font-bold">Backtesting — Validación Histórica</h1>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4">
        {(['BVN', 'SCCO'] as Ticker[]).map((t) => (
          <button
            key={t}
            onClick={() => setTicker(t)}
            className={`px-6 py-2 rounded-xl font-bold transition-all ${
              ticker === t
                ? 'bg-[#d9ecff] text-[#0b477d] border-2 border-[#4aa3ff]'
                : 'bg-card text-[#c7c7c2] border border-border'
            }`}
          >
            {t}
          </button>
        ))}
        <div className="flex gap-2">
          {PERIODS.map(({ label, dias: d }) => (
            <button
              key={d}
              onClick={() => setDias(d)}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
                dias === d
                  ? 'bg-[#1a3a5f] text-white border-2 border-[#4aa3ff]'
                  : 'bg-card text-[#c7c7c2] border border-border'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <button
          onClick={handleRun}
          disabled={loading}
          className="px-8 py-2 rounded-xl font-bold bg-[#4aa3ff] text-white hover:bg-[#2d8ae8] disabled:opacity-50 transition-all"
        >
          {loading ? 'Ejecutando...' : 'Ejecutar backtest'}
        </button>
      </div>

      {error && (
        <div className="bg-sell-bg border border-sell-border rounded-xl p-4 text-sell-text">{error}</div>
      )}

      {result && (
        <>
          {/* Header métricas */}
          <p className="text-white font-semibold">
            {result.ticker} — {result.periodo.inicio} al {result.periodo.fin} ({result.periodo.dias} días)
          </p>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-card border border-border rounded-2xl p-6">
              <p className="text-[#bfbfba] font-semibold">Estrategia PSO</p>
              <p className="text-white text-4xl font-bold mt-2">
                {result.estrategia_pso.retorno_total.toFixed(2)}%
              </p>
              <p className="text-muted text-sm mt-1">Retorno total</p>
            </div>
            <div className="bg-card border border-border rounded-2xl p-6">
              <p className="text-[#bfbfba] font-semibold">Buy &amp; Hold</p>
              <p className="text-white text-4xl font-bold mt-2">
                {result.buy_hold.retorno_total.toFixed(2)}%
              </p>
              <p className="text-muted text-sm mt-1">Retorno total</p>
            </div>
            <div className="bg-card border border-border rounded-2xl p-6">
              <p className="text-[#bfbfba] font-semibold">Ganador</p>
              <p
                className="text-4xl font-bold mt-2"
                style={{ color: result.comparacion.ganador === 'PSO' ? '#19c39c' : '#f0a92f' }}
              >
                {result.comparacion.ganador}
              </p>
              <p className="text-muted text-sm mt-1">
                Diferencia: {result.comparacion.diferencia_retorno.toFixed(2)}%
              </p>
            </div>
          </div>

          {/* Gráfico de capital */}
          <div className="bg-card border border-border rounded-2xl p-6">
            <h2 className="text-white font-bold text-lg mb-4">Evolución del Capital: PSO vs Buy &amp; Hold</h2>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2c" />
                <XAxis dataKey="fecha" tick={{ fill: '#6b6b65', fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fill: '#6b6b65', fontSize: 11 }} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#1c1c1b', border: '1px solid #2e2e2c', color: '#fff' }} />
                <Legend wrapperStyle={{ color: '#bfbfba' }} />
                <Line type="monotone" dataKey="PSO" stroke="#4aa3ff" dot={false} strokeWidth={3} />
                <Line type="monotone" dataKey="BuyHold" name="Buy & Hold" stroke="#f0a92f" dot={false} strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Métricas de riesgo */}
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: 'Sharpe Ratio', value: result.estrategia_pso.sharpe_ratio.toFixed(2), sub: 'Anualizado' },
              { label: 'Max Drawdown', value: `${result.estrategia_pso.max_drawdown.toFixed(2)}%`, sub: 'Pérdida máxima' },
              { label: 'Win Rate', value: `${result.estrategia_pso.win_rate.toFixed(1)}%`, sub: 'Operaciones ganadoras' },
              { label: 'Operaciones', value: result.estrategia_pso.num_operaciones, sub: 'Total ejecutadas' },
            ].map(({ label, value, sub }) => (
              <div key={label} className="bg-card border border-border rounded-2xl p-6">
                <p className="text-[#bfbfba] font-semibold">{label}</p>
                <p className="text-white text-3xl font-bold mt-2">{value}</p>
                <p className="text-muted text-sm mt-1">{sub}</p>
              </div>
            ))}
          </div>

          {/* Tabla de operaciones */}
          <div className="bg-card border border-border rounded-2xl p-6">
            <h2 className="text-white font-bold text-lg mb-4">Historial de Operaciones</h2>
            {result.operaciones.length === 0 ? (
              <p className="text-muted text-sm">No hubo operaciones en este período.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-muted border-b border-border">
                      <th className="text-left py-2 pr-4">Fecha</th>
                      <th className="text-left py-2 pr-4">Tipo</th>
                      <th className="text-right py-2 pr-4">Precio</th>
                      <th className="text-right py-2">Ganancia</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.operaciones.map((op, i) => (
                      <tr key={i} className="border-b border-border text-white">
                        <td className="py-2 pr-4">{op.fecha}</td>
                        <td className={`py-2 pr-4 font-bold ${op.tipo === 'COMPRA' ? 'text-buy-text' : 'text-sell-text'}`}>
                          {op.tipo}
                        </td>
                        <td className="py-2 pr-4 text-right">${op.precio.toFixed(2)}</td>
                        <td className={`py-2 text-right font-semibold ${(op.ganancia ?? 0) >= 0 ? 'text-buy-text' : 'text-sell-text'}`}>
                          {op.ganancia !== undefined ? `${op.ganancia >= 0 ? '+' : ''}$${op.ganancia.toFixed(2)}` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

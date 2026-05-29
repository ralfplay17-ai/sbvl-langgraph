import { useState, useEffect } from 'react'
import { runAnalysis, getHistory } from '../lib/api'
import type { AnalysisResult, HistoryItem } from '../types'
import { SignalCard } from '../components/SignalCard'
import { AgentStatus } from '../components/AgentStatus'
import { PSOWeights } from '../components/PSOWeights'
import { AgentDetail } from '../components/AgentDetail'
import { HistoryPanel } from '../components/HistoryPanel'
import { ChatPanel } from '../components/ChatPanel'

type Ticker = 'BVN' | 'SCCO'

export function Dashboard() {
  const [ticker, setTicker] = useState<Ticker>('BVN')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [elapsed, setElapsed] = useState<number | null>(null)
  const [timer, setTimer] = useState(0)

  useEffect(() => {
    getHistory(undefined, 10).then(setHistory).catch(() => {})
  }, [])

  useEffect(() => {
    if (!loading) return
    setTimer(0)
    const interval = setInterval(() => setTimer(s => s + 1), 1000)
    return () => clearInterval(interval)
  }, [loading])

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    setElapsed(null)
    const start = Date.now()
    try {
      const data = await runAnalysis(ticker)
      setResult(data)
      setElapsed(Math.round((Date.now() - start) / 1000))
      getHistory(undefined, 10).then(setHistory).catch(() => {})
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-white text-3xl font-bold">Soporte de decisión — Mineras BVL</h1>
          <p className="text-muted text-sm mt-1">Sistema multiagente con PSO Consensus Engine</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="bg-buy-bg text-buy-text px-4 py-2 rounded-xl text-sm font-bold">EN VIVO</span>
          {loading && (
            <span className="text-[#f0a92f] text-xs font-mono">⏱ {timer}s transcurridos...</span>
          )}
          {!loading && elapsed !== null && (
            <span className="text-muted text-xs font-mono">Completado en {elapsed}s</span>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        {(['BVN', 'SCCO'] as Ticker[]).map((t) => (
          <button
            key={t}
            onClick={() => setTicker(t)}
            className={`px-6 py-2 rounded-xl font-bold transition-all ${
              ticker === t
                ? 'bg-[#d9ecff] text-[#0b477d] border-2 border-[#4aa3ff]'
                : 'bg-card text-[#c7c7c2] border border-border hover:border-[#4aa3ff]'
            }`}
          >
            {t}
          </button>
        ))}
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="ml-4 px-8 py-2 rounded-xl font-bold bg-[#4aa3ff] text-white hover:bg-[#2d8ae8] disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {loading ? 'Analizando...' : 'Analizar'}
        </button>
      </div>

      {error && (
        <div className="bg-sell-bg border border-sell-border rounded-xl p-4 text-sell-text">
          {error}
        </div>
      )}

      {loading && (
        <div className="bg-card border border-border rounded-2xl p-12 text-center">
          <div className="animate-pulse">
            <p className="text-white text-xl font-bold">Ejecutando análisis multiagente...</p>
            <p className="text-muted mt-2">4 agentes en paralelo → PSO → Coordinador</p>
          </div>
        </div>
      )}

      {result && !loading && (
        <>
          {/* Métricas superiores */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-card border border-border rounded-2xl p-6">
              <p className="text-[#bfbfba] font-semibold">Ticker analizado</p>
              <p className="text-white text-4xl font-bold mt-2">{result.ticker}</p>
              <p className="text-muted text-sm mt-1">Acción minera BVL</p>
            </div>
            <div className="bg-card border border-border rounded-2xl p-6">
              <p className="text-[#bfbfba] font-semibold">Score final PSO</p>
              <p className="text-white text-4xl font-bold mt-2">{result.score_final.toFixed(4)}</p>
              <p className="text-muted text-sm mt-1">Rango: -1 a 1</p>
            </div>
            <div className="bg-card border border-border rounded-2xl p-6">
              <p className="text-[#bfbfba] font-semibold">Confianza final</p>
              <p className="text-white text-4xl font-bold mt-2">{Math.round(result.confianza_final * 100)}%</p>
              <p className="text-muted text-sm mt-1">Nivel: {result.dashboard.nivel_confianza}</p>
            </div>
          </div>

          {/* Señal + Agentes */}
          <div className="grid grid-cols-2 gap-6">
            <AgentStatus
              senales={result.senales_agentes}
              confianzas={result.confianzas_agentes}
              pesos={result.pesos_utilizados}
            />
            <div className="space-y-4">
              <SignalCard
                senal={result.senal_final}
                score={result.score_final}
                confianza={result.confianza_final}
              />
              <div className="bg-card border border-border rounded-2xl p-6">
                <h3 className="text-white font-bold text-lg mb-3">¿Por qué esta señal?</h3>
                {result.factores_clave.map((f, i) => (
                  <p key={i} className="text-[#d0d0cc] text-base py-1">• {f}</p>
                ))}
              </div>
            </div>
          </div>

          {/* Pesos PSO */}
          <PSOWeights pesos={result.pesos_utilizados} />

          {/* Detalle agentes */}
          <AgentDetail
            detalle={result.detalle_agentes}
            scores={result.scores_agentes}
            confianzas={result.confianzas_agentes}
          />

          {/* Limitaciones */}
          {result.limitaciones.length > 0 && result.limitaciones[0] !== 'Sin limitaciones relevantes' && (
            <div className="space-y-2">
              <h2 className="text-white text-xl font-bold">Limitaciones</h2>
              {result.limitaciones.map((lim, i) => (
                <div key={i} className="bg-hold-bg border border-hold-border rounded-xl p-3 text-hold-text text-sm">
                  ⚠ {lim}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Historial + Chat */}
      <div className="grid grid-cols-2 gap-6">
        <HistoryPanel history={history} onSelect={(item) => console.log('Selected:', item)} />
        <ChatPanel />
      </div>
    </div>
  )
}

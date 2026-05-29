export type Senal = 'COMPRAR' | 'MANTENER' | 'VENDER'

export interface AgentDetail {
  senal: Senal
  score: number
  confianza: number
  resumen: string
}

export interface AnalysisResult {
  agente: string
  ticker: string
  senal_final: Senal
  score_final: number
  confianza_final: number
  dashboard: {
    color_senal: 'verde' | 'amarillo' | 'rojo'
    estado: 'favorable' | 'neutral' | 'desfavorable'
    resumen_corto: string
    nivel_confianza: 'alta' | 'media' | 'baja'
  }
  pesos_utilizados: {
    tecnico: number
    commodities: number
    sentimiento: number
    riesgo: number
  }
  scores_agentes: {
    tecnico: number
    commodities: number
    sentimiento: number
    riesgo: number
  }
  confianzas_agentes: {
    tecnico: number
    commodities: number
    sentimiento: number
    riesgo: number
  }
  senales_agentes: {
    tecnico: Senal
    commodities: Senal
    sentimiento: Senal
    riesgo: Senal
  }
  factores_clave: string[]
  detalle_agentes: {
    tecnico: AgentDetail
    commodities: AgentDetail
    sentimiento: AgentDetail
    riesgo: AgentDetail
  }
  limitaciones: string[]
  pso: {
    algoritmo: string
    particulas: number
    iteraciones: number
    costo_optimizacion: number | null
  }
}

export interface HistoryItem {
  id: string
  ticker: string
  senal_final: Senal
  score_final: number
  confianza_final: number
  factores_clave: string[]
  created_at: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface ChatSession {
  session_id: string
  messages: ChatMessage[]
}

export interface BacktestResult {
  ticker: string
  periodo: { inicio: string; fin: string; dias: number }
  estrategia_pso: {
    capital_inicial: number
    capital_final: number
    retorno_total: number
    sharpe_ratio: number
    max_drawdown: number
    win_rate: number
    num_operaciones: number
    historial_capital: { fecha: string; capital: number }[]
  }
  buy_hold: {
    capital_inicial: number
    capital_final: number
    retorno_total: number
    historial_capital: { fecha: string; capital: number }[]
  }
  comparacion: { diferencia_retorno: number; ganador: string }
  operaciones: { fecha: string; tipo: string; precio: number; ganancia?: number }[]
}

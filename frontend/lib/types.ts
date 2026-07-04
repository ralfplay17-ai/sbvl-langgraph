export type Senal = "COMPRAR" | "MANTENER" | "VENDER";

export interface PSOConfig {
  n_particles: number;
  iters: number;
  c1: number;
  c2: number;
  w: number;
}

export interface AgentResult {
  agente: string;
  ticker: string;
  senal: Senal;
  score: number;
  confianza: number;
  datos_usados: string;
  resumen: string;
}

export interface AnalysisResult {
  ticker: string;
  senal_final: Senal;
  score_final: number;
  confianza_final: number;
  pesos_utilizados: Record<string, number>;
  historial_convergencia: number[];
  pso_config: Partial<PSOConfig>;
  detalle_agentes: Record<string, AgentResult>;
  factores_clave: string[];
  error_sistema?: string | null;
  tiempo_ejecucion_s?: number;
  dashboard: {
    nivel_confianza: "alta" | "media" | "baja";
    color_senal: "verde" | "amarillo" | "rojo";
    resumen_corto: string;
  };
}

export interface SSEEvent {
  type: "start" | "agent_start" | "agent_complete" | "pso_complete" | "final" | "error" | "close" | "done";
  agent?: string;
  result?: AnalysisResult | Record<string, unknown>;
  ticker?: string;
  message?: string;
}

export interface PrecioRT {
  ticker: string;
  precio: number | null;
  variacion_pct: number | null;
  volumen: number | null;
  moneda: string;
  nombre?: string;
  error?: string;
}

export interface HistoricoPoint {
  fecha: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
  rsi: number | null;
  macd: number | null;
  signal: number | null;
  sma20: number | null;
  sma50: number | null;
}

export interface CommodityData {
  label: string;
  unit: string;
  precio: number;
  cambio_dia_pct: number;
  tendencia_5d_pct: number;
  closes: number[];
  dates: string[];
  fuente: string;
  error?: string;
}

export interface BacktestResult {
  ticker: string;
  periodo: { inicio: string; fin: string; dias: number };
  estrategia_pso: {
    capital_final: number;
    retorno_total: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    num_operaciones: number;
    historial_capital: { fecha: string; capital: number }[];
  };
  buy_hold: {
    capital_final: number;
    retorno_total: number;
    historial_capital: { fecha: string; capital: number }[];
  };
  comparacion: { diferencia: number; ganador: string };
  benchmark: { ticker: string; retorno_total: number | null; sharpe_ratio: number | null };
  operaciones: { fecha: string; tipo: string; precio: number; ganancia?: number }[];
  error?: string;
}

export interface Noticia {
  titulo: string;
  fecha?: string;
  publicado?: string;
  fuente?: string;
  score?: number;
  label?: string;
  resumen: string;
  url?: string;
  link?: string;
}

export interface TickerOption {
  value: string;
  label: string;
}

export interface HistoryRecord {
  id: string;
  ticker: string;
  senal_final: Senal;
  score_final: number;
  confianza_final: number;
  pso_config: Partial<PSOConfig>;
  agentes_result: Record<string, AgentResult>;
  pso_result: {
    pesos: Record<string, number>;
    convergencia: number[];
  };
  created_at: string;
}

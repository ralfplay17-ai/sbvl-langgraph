import axios, { AxiosError } from 'axios'
import type { AnalysisResult, HistoryItem, BacktestResult, ChatMessage } from '../types'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

const client = axios.create({ baseURL: BASE_URL })

client.interceptors.response.use(
  res => res,
  (err: AxiosError<{ detail: string }>) => {
    const detail = err.response?.data?.detail
    if (detail) throw new Error(detail)
    throw err
  }
)

export async function runAnalysis(ticker: string): Promise<AnalysisResult> {
  const { data } = await client.post('/analysis/run', { ticker, include_news_prefetch: true })
  return data
}

export async function getHistory(ticker?: string, limit = 20): Promise<HistoryItem[]> {
  const params: Record<string, string | number> = { limit }
  if (ticker) params.ticker = ticker
  const { data } = await client.get('/analysis/history', { params })
  return data
}

export async function runBacktest(ticker: string, dias: number): Promise<BacktestResult> {
  const { data } = await client.post('/backtest/run', { ticker, dias })
  return data
}

export async function newChatSession(): Promise<string> {
  const { data } = await client.post('/chat/new-session')
  return data.session_id
}

export async function sendChatMessage(session_id: string, message: string): Promise<string> {
  const { data } = await client.post('/chat/message', { session_id, message })
  return data.response
}

export async function getChatHistory(session_id: string): Promise<ChatMessage[]> {
  const { data } = await client.get(`/chat/history/${session_id}`)
  return data.messages
}

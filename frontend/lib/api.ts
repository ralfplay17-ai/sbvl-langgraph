import type {
  AnalysisResult, BacktestResult, CommodityData,
  HistoricoPoint, Noticia, PrecioRT, SSEEvent, TickerOption, PSOConfig,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// ─── SSE Stream ───────────────────────────────────────────────────────────────

export function streamAnalysis(
  ticker: string,
  pso_config: PSOConfig,
  onEvent: (event: SSEEvent) => void,
  onError: (err: Error) => void,
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, pso_config }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6)) as SSEEvent;
              onEvent(event);
            } catch {
              // ignorar líneas malformadas
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onError(err as Error);
      }
    }
  })();

  return () => controller.abort();
}

// ─── Market ───────────────────────────────────────────────────────────────────

export async function getTickers(): Promise<TickerOption[]> {
  const data = await get<{ tickers: TickerOption[] }>("/api/market/tickers");
  return data.tickers;
}

export async function getPrecio(ticker: string): Promise<PrecioRT> {
  return get<PrecioRT>(`/api/market/price/${ticker}`);
}

export async function getHistorico(ticker: string, dias = 60): Promise<HistoricoPoint[]> {
  const data = await get<{ ticker: string; historico: HistoricoPoint[] }>(
    `/api/market/historico/${ticker}?dias=${dias}`
  );
  return data.historico ?? [];
}

export async function getCommodities(): Promise<Record<string, CommodityData>> {
  return get<Record<string, CommodityData>>("/api/market/commodities");
}

export async function getNoticias(ticker: string): Promise<{ alpha_vantage: Noticia[]; google_news: Noticia[] }> {
  return get(`/api/market/noticias/${ticker}`);
}

// ─── Backtest ─────────────────────────────────────────────────────────────────

export async function runBacktest(ticker: string, dias: number): Promise<BacktestResult> {
  return post<BacktestResult>("/api/backtest", { ticker, dias });
}

// ─── History ──────────────────────────────────────────────────────────────────

export async function getHistory(ticker?: string, limit = 20): Promise<AnalysisResult[]> {
  const qs = ticker ? `?ticker=${ticker}&limit=${limit}` : `?limit=${limit}`;
  return get<AnalysisResult[]>(`/api/history${qs}`);
}

import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

interface DataPoint {
  fecha: string
  close: number
  sma20?: number | null
  sma50?: number | null
  rsi?: number | null
  macd?: number | null
  signal?: number | null
}

interface Props {
  data: DataPoint[]
  ticker: string
}

export function PriceChart({ data, ticker }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-card border border-border rounded-2xl p-6 h-64 flex items-center justify-center">
        <p className="text-muted">Sin datos históricos disponibles</p>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-2xl p-6 space-y-6">
      <h2 className="text-white text-xl font-bold">{ticker} — Precio y Medias Móviles</h2>

      {/* Precio */}
      <ResponsiveContainer width="100%" height={250}>
        <ComposedChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2c" />
          <XAxis dataKey="fecha" tick={{ fill: '#6b6b65', fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fill: '#6b6b65', fontSize: 11 }} tickLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1c1c1b', border: '1px solid #2e2e2c', color: '#fff' }}
          />
          <Legend wrapperStyle={{ color: '#bfbfba' }} />
          <Line type="monotone" dataKey="close" name="Precio" stroke="#4aa3ff" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="sma20" name="SMA20" stroke="#f0a92f" dot={false} strokeWidth={1.5} connectNulls />
          <Line type="monotone" dataKey="sma50" name="SMA50" stroke="#d94841" dot={false} strokeWidth={1.5} connectNulls />
        </ComposedChart>
      </ResponsiveContainer>

      {/* RSI */}
      <h3 className="text-white font-semibold">RSI (14)</h3>
      <ResponsiveContainer width="100%" height={120}>
        <ComposedChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2c" />
          <XAxis dataKey="fecha" tick={{ fill: '#6b6b65', fontSize: 11 }} tickLine={false} />
          <YAxis domain={[0, 100]} tick={{ fill: '#6b6b65', fontSize: 11 }} tickLine={false} />
          <Tooltip contentStyle={{ backgroundColor: '#1c1c1b', border: '1px solid #2e2e2c', color: '#fff' }} />
          <ReferenceLine y={70} stroke="#d94841" strokeDasharray="4 4" />
          <ReferenceLine y={30} stroke="#5ca22d" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="rsi" name="RSI" stroke="#19c39c" dot={false} strokeWidth={2} connectNulls />
        </ComposedChart>
      </ResponsiveContainer>

      {/* MACD */}
      <h3 className="text-white font-semibold">MACD</h3>
      <ResponsiveContainer width="100%" height={120}>
        <ComposedChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2e2e2c" />
          <XAxis dataKey="fecha" tick={{ fill: '#6b6b65', fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fill: '#6b6b65', fontSize: 11 }} tickLine={false} />
          <Tooltip contentStyle={{ backgroundColor: '#1c1c1b', border: '1px solid #2e2e2c', color: '#fff' }} />
          <Legend wrapperStyle={{ color: '#bfbfba' }} />
          <Line type="monotone" dataKey="macd" name="MACD" stroke="#4aa3ff" dot={false} strokeWidth={2} connectNulls />
          <Line type="monotone" dataKey="signal" name="Signal" stroke="#f0a92f" dot={false} strokeWidth={2} connectNulls />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

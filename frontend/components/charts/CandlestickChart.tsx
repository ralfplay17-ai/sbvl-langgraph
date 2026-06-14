"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import type { HistoricoPoint } from "@/lib/types";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface Props {
  data: HistoricoPoint[];
  ticker: string;
}

export default function CandlestickChart({ data, ticker }: Props) {
  if (!data || data.length < 5) {
    return (
      <div className="flex items-center justify-center h-64 text-zinc-500 text-sm">
        Sin datos históricos suficientes para graficar.
      </div>
    );
  }

  const dates  = data.map((d) => d.fecha);
  const ohlc   = data.map((d) => [d.open, d.close, d.low, d.high]);
  const rsi    = data.map((d) => d.rsi);
  const macd   = data.map((d) => d.macd);
  const signal = data.map((d) => d.signal);
  const hist   = data.map((d) => (d.macd ?? 0) - (d.signal ?? 0));
  const sma20  = data.map((d) => d.sma20);
  const sma50  = data.map((d) => d.sma50);

  const option: EChartsOption = {
    backgroundColor: "#111",
    animation: false,
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      backgroundColor: "#1a1a1a",
      borderColor: "#333",
      textStyle: { color: "#ccc", fontSize: 12 },
    },
    legend: {
      top: 4,
      textStyle: { color: "#888", fontSize: 11 },
      data: ["Precio", "SMA 20", "SMA 50", "RSI", "MACD", "Señal"],
    },
    grid: [
      { left: 60, right: 60, top: 40, height: "50%" },
      { left: 60, right: 60, top: "60%", height: "15%" },
      { left: 60, right: 60, top: "80%", height: "15%" },
    ],
    xAxis: [
      { type: "category", data: dates, gridIndex: 0, axisLine: { lineStyle: { color: "#333" } }, axisLabel: { color: "#666" }, boundaryGap: false },
      { type: "category", data: dates, gridIndex: 1, axisLabel: { show: false }, axisLine: { lineStyle: { color: "#333" } } },
      { type: "category", data: dates, gridIndex: 2, axisLabel: { color: "#666", fontSize: 10 }, axisLine: { lineStyle: { color: "#333" } } },
    ],
    yAxis: [
      { gridIndex: 0, splitLine: { lineStyle: { color: "#1f1f1f" } }, axisLabel: { color: "#666" } },
      { gridIndex: 1, min: 0, max: 100, splitLine: { lineStyle: { color: "#1f1f1f" } }, axisLabel: { color: "#666", fontSize: 10 } },
      { gridIndex: 2, splitLine: { lineStyle: { color: "#1f1f1f" } }, axisLabel: { color: "#666", fontSize: 10 } },
    ],
    dataZoom: [
      { type: "inside", xAxisIndex: [0, 1, 2], start: 40, end: 100 },
      { type: "slider", xAxisIndex: [0, 1, 2], bottom: 4, height: 16,
        borderColor: "#333", backgroundColor: "#111", dataBackground: { lineStyle: { color: "#333" } } },
    ],
    series: [
      {
        name: "Precio",
        type: "candlestick",
        xAxisIndex: 0, yAxisIndex: 0,
        data: ohlc,
        itemStyle: {
          color: "#22c55e", color0: "#ef4444",
          borderColor: "#22c55e", borderColor0: "#ef4444",
        },
      },
      {
        name: "SMA 20",
        type: "line", xAxisIndex: 0, yAxisIndex: 0,
        data: sma20,
        smooth: true,
        lineStyle: { color: "#fbbf24", width: 1.5, type: "dotted" },
        showSymbol: false,
      },
      {
        name: "SMA 50",
        type: "line", xAxisIndex: 0, yAxisIndex: 0,
        data: sma50,
        smooth: true,
        lineStyle: { color: "#f87171", width: 1.5, type: "dotted" },
        showSymbol: false,
      },
      {
        name: "RSI",
        type: "line", xAxisIndex: 1, yAxisIndex: 1,
        data: rsi,
        smooth: true,
        lineStyle: { color: "#34d399", width: 2 },
        showSymbol: false,
        markLine: {
          silent: true,
          lineStyle: { color: "#ef4444", type: "dashed", width: 1 },
          data: [{ yAxis: 70 }, { yAxis: 30 }],
          label: { color: "#888", fontSize: 10 },
        },
      },
      {
        name: "MACD",
        type: "line", xAxisIndex: 2, yAxisIndex: 2,
        data: macd, smooth: true,
        lineStyle: { color: "#60a5fa", width: 2 },
        showSymbol: false,
      },
      {
        name: "Señal",
        type: "line", xAxisIndex: 2, yAxisIndex: 2,
        data: signal, smooth: true,
        lineStyle: { color: "#fbbf24", width: 2 },
        showSymbol: false,
      },
      {
        name: "Histograma",
        type: "bar", xAxisIndex: 2, yAxisIndex: 2,
        data: hist.map((v) => ({
          value: v,
          itemStyle: { color: (v ?? 0) >= 0 ? "#22c55e" : "#ef4444", opacity: 0.6 },
        })),
      },
    ],
  };

  return (
    <div className="w-full">
      <p className="text-xs text-zinc-500 mb-1">{ticker} — Candlestick · RSI · MACD</p>
      <ReactECharts option={option} style={{ height: 600 }} theme="dark" />
    </div>
  );
}

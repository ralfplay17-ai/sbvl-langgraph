"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import type { BacktestResult } from "@/lib/types";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface Props {
  data: BacktestResult;
}

export default function BacktestChart({ data }: Props) {
  const pso = data.estrategia_pso.historial_capital;
  const bh  = data.buy_hold.historial_capital;

  const option: EChartsOption = {
    backgroundColor: "#111",
    animation: false,
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1a1a1a",
      borderColor: "#333",
      textStyle: { color: "#ccc", fontSize: 12 },
      formatter: (params: unknown) => {
        const ps = params as { seriesName: string; value: number; axisValue: string }[];
        let s = `<b>${ps[0].axisValue}</b><br/>`;
        ps.forEach((p) => { s += `${p.seriesName}: $${p.value.toFixed(0)}<br/>`; });
        return s;
      },
    },
    legend: {
      top: 4,
      textStyle: { color: "#888", fontSize: 11 },
      data: ["Estrategia PSO", "Buy & Hold"],
    },
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
    xAxis: {
      type: "category",
      data: pso.map((d) => d.fecha),
      axisLabel: { color: "#666", fontSize: 10 },
      axisLine: { lineStyle: { color: "#333" } },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#1f1f1f" } },
      axisLabel: { color: "#666", formatter: (v: number) => `$${v.toFixed(0)}` },
    },
    dataZoom: [
      { type: "inside", start: 0, end: 100 },
      { type: "slider", bottom: 4, height: 16, borderColor: "#333", backgroundColor: "#111" },
    ],
    series: [
      {
        name: "Estrategia PSO",
        type: "line",
        data: pso.map((d) => d.capital),
        smooth: true,
        lineStyle: { color: "#60a5fa", width: 3 },
        showSymbol: false,
        areaStyle: { color: "rgba(96,165,250,0.06)" },
      },
      {
        name: "Buy & Hold",
        type: "line",
        data: bh.map((d) => d.capital),
        smooth: true,
        lineStyle: { color: "#fbbf24", width: 3 },
        showSymbol: false,
        areaStyle: { color: "rgba(251,191,36,0.04)" },
      },
    ],
  };

  return (
    <ReactECharts option={option} style={{ height: 400 }} theme="dark" />
  );
}

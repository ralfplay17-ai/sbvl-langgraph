"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface Props {
  data: number[];
}

export default function ConvergenceChart({ data }: Props) {
  if (!data || data.length < 2) return null;

  const yMin = Math.min(...data);
  const yMax = Math.max(...data);
  const margin = Math.max(Math.abs(yMax - yMin) * 0.2, 0.02);

  const option: EChartsOption = {
    backgroundColor: "#111",
    animation: false,
    tooltip: {
      trigger: "axis",
      formatter: (params: unknown) => {
        const p = (params as { dataIndex: number; value: number }[])[0];
        return `Iter ${p.dataIndex + 1}: ${p.value.toFixed(6)}`;
      },
      backgroundColor: "#1a1a1a",
      borderColor: "#333",
      textStyle: { color: "#ccc", fontSize: 11 },
    },
    grid: { left: 60, right: 80, top: 32, bottom: 32 },
    xAxis: {
      type: "category",
      data: data.map((_, i) => i + 1),
      axisLabel: { color: "#666", fontSize: 10 },
      axisLine: { lineStyle: { color: "#333" } },
      name: "Iteración",
      nameTextStyle: { color: "#666", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      min: yMin - margin,
      max: yMax + margin,
      splitLine: { lineStyle: { color: "#1f1f1f" } },
      axisLabel: { color: "#666", fontSize: 10, formatter: (v: number) => v.toFixed(4) },
      name: "Costo",
      nameTextStyle: { color: "#666", fontSize: 10 },
    },
    series: [
      {
        type: "line",
        data,
        smooth: false,
        lineStyle: { color: "#60a5fa", width: 2 },
        areaStyle: { color: "rgba(96,165,250,0.08)" },
        showSymbol: false,
        markLine: {
          silent: true,
          data: [{ yAxis: yMin }],
          lineStyle: { color: "#f59e0b", type: "dotted", width: 1 },
          label: {
            formatter: `Mín: ${yMin.toFixed(4)}`,
            color: "#f59e0b",
            fontSize: 10,
            position: "end",
          },
        },
      },
    ],
  };

  return (
    <div className="w-full">
      <p className="text-xs text-zinc-500 mb-1">Convergencia PSO — Costo por iteración</p>
      <ReactECharts option={option} style={{ height: 200 }} theme="dark" />
    </div>
  );
}

"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface Props {
  closes: number[];
  dates: string[];
  color?: string;
}

export default function SparklineChart({ closes, dates, color = "#60a5fa" }: Props) {
  if (!closes || closes.length < 2) return null;

  const option: EChartsOption = {
    backgroundColor: "transparent",
    animation: false,
    grid: { left: 0, right: 0, top: 0, bottom: 0 },
    xAxis: { type: "category", data: dates, show: false },
    yAxis: { type: "value", show: false },
    series: [
      {
        type: "line",
        data: closes,
        smooth: true,
        lineStyle: { color, width: 1.5 },
        areaStyle: { color: color + "18" },
        showSymbol: false,
      },
    ],
    tooltip: { show: false },
  };

  return (
    <ReactECharts option={option} style={{ height: 64 }} theme="dark" />
  );
}

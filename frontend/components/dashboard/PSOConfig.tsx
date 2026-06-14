"use client";

import { useState } from "react";
import * as Slider from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";
import type { PSOConfig } from "@/lib/types";

interface Props {
  value: PSOConfig;
  onChange: (cfg: PSOConfig) => void;
}

interface SliderDef {
  key: keyof PSOConfig;
  label: string;
  min: number;
  max: number;
  step: number;
  format?: (v: number) => string;
}

const SLIDERS: SliderDef[] = [
  { key: "n_particles", label: "Partículas",  min: 10,  max: 200, step: 10 },
  { key: "iters",       label: "Iteraciones", min: 50,  max: 500, step: 50 },
  { key: "c1",          label: "c₁ Cognitivo",min: 0.1, max: 2.5, step: 0.1, format: (v) => v.toFixed(1) },
  { key: "c2",          label: "c₂ Social",   min: 0.1, max: 2.5, step: 0.1, format: (v) => v.toFixed(1) },
  { key: "w",           label: "w Inercia",   min: 0.1, max: 1.5, step: 0.05, format: (v) => v.toFixed(2) },
];

export default function PSOConfig({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-zinc-300 hover:bg-zinc-800/40 transition-colors"
      >
        <span>Configuración PSO</span>
        <span className="text-zinc-600">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4 bg-surface-2">
          {SLIDERS.map(({ key, label, min, max, step, format }) => (
            <div key={key}>
              <div className="flex justify-between text-xs text-zinc-400 mb-1.5">
                <span>{label}</span>
                <span className="font-mono text-zinc-200">
                  {format ? format(value[key] as number) : value[key]}
                </span>
              </div>
              <Slider.Root
                min={min} max={max} step={step}
                value={[value[key] as number]}
                onValueChange={([v]) => onChange({ ...value, [key]: v })}
                className="relative flex items-center w-full h-4"
              >
                <Slider.Track className="relative h-1 flex-1 rounded bg-zinc-700">
                  <Slider.Range className="absolute h-full rounded bg-blue-500" />
                </Slider.Track>
                <Slider.Thumb className="block w-4 h-4 rounded-full bg-blue-400 border-2 border-blue-600 shadow focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </Slider.Root>
              <div className="flex justify-between text-[10px] text-zinc-600 mt-0.5">
                <span>{format ? format(min) : min}</span>
                <span>{format ? format(max) : max}</span>
              </div>
            </div>
          ))}
          <button
            onClick={() => onChange({ n_particles: 50, iters: 100, c1: 0.5, c2: 0.3, w: 0.9 })}
            className="w-full text-xs text-zinc-500 hover:text-zinc-300 transition-colors py-1 border border-border rounded"
          >
            Restaurar valores por defecto
          </button>
        </div>
      )}
    </div>
  );
}

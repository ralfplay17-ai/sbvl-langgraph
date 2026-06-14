import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0a",
        surface: "#111111",
        "surface-2": "#1a1a1a",
        border: "#2a2a2a",
        buy: "#22c55e",
        sell: "#ef4444",
        hold: "#eab308",
        "buy-bg": "#0d2e1a",
        "sell-bg": "#2e0d0d",
        "hold-bg": "#2c2200",
      },
      borderRadius: { DEFAULT: "0.5rem" },
    },
  },
  plugins: [],
};

export default config;

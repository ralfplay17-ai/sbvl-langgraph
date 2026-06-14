import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dashboard BVL — Análisis Minero",
  description: "Sistema de análisis multiagente para el sector minero peruano (BVL)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark">
      <body className="bg-background text-zinc-200 min-h-screen">
        {children}
      </body>
    </html>
  );
}

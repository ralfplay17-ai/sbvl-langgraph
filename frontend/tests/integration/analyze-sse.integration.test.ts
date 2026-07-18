/**
 * Prueba de integración del flujo SSE: streamAnalysis() (frontend, parseo
 * manual de "data: ..." por línea con ReadableStream) contra el stream real
 * que emite POST /api/analyze en el backend. Es la parte más delicada del
 * contrato frontend-backend porque el parseo de SSE es hecho a mano (no usa
 * EventSource nativo), así que vale la pena probarlo contra bytes reales.
 */
import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { streamAnalysis } from "../../lib/api";
import type { SSEEvent } from "../../lib/types";
import { ensureBackendUp } from "./helpers";

beforeAll(ensureBackendUp);

// Se guarda acá el `stop` de la conexión SSE activa para poder abortarla
// SIEMPRE en afterEach, incluso si el propio timeout de Vitest corta el test
// antes que nuestro timeout interno (si no, el stream queda abierto colgando
// el proceso -- se detectó exactamente este problema al validar el test).
let stopActivo: (() => void) | null = null;

afterEach(() => {
  stopActivo?.();
  stopActivo = null;
});

function recolectarEventos(ticker: string, timeoutMs = 15_000): Promise<SSEEvent[]> {
  return new Promise((resolve, reject) => {
    const eventos: SSEEvent[] = [];
    const timeout = setTimeout(() => {
      reject(new Error(`Timeout esperando el cierre del stream SSE (${eventos.length} eventos recibidos)`));
    }, timeoutMs);

    stopActivo = streamAnalysis(
      ticker,
      { n_particles: 10, iters: 50, c1: 0.5, c2: 0.3, w: 0.9 },
      (event) => {
        eventos.push(event);
        if (event.type === "close") {
          clearTimeout(timeout);
          resolve(eventos);
        }
      },
      (err) => {
        clearTimeout(timeout);
        reject(err);
      },
    );
  });
}

describe("streamAnalysis()", () => {
  it("recibe el evento inicial 'start' con el ticker correcto", async () => {
    const eventos = await recolectarEventos("BVN");
    expect(eventos[0]).toEqual({ type: "start", ticker: "BVN" });
  });

  it("termina siempre con el evento 'close'", async () => {
    const eventos = await recolectarEventos("BVN");
    expect(eventos.at(-1)?.type).toBe("close");
  });

  it("llega a un estado terminal reconocible: 'final' (con result) o 'error' (con message)", async () => {
    const eventos = await recolectarEventos("BVN");

    const final = eventos.find((e) => e.type === "final");
    const error = eventos.find((e) => e.type === "error");

    expect(final || error).toBeDefined();

    if (error) {
      expect(typeof error.message).toBe("string");
      expect(error.message!.length).toBeGreaterThan(0);
    }
    if (final) {
      expect(final.result).toBeDefined();
    }
  });

  it("cada evento parseado es JSON válido con un campo 'type' conocido", async () => {
    const eventos = await recolectarEventos("BVN");
    const tiposValidos = new Set([
      "start", "agent_start", "agent_complete", "pso_complete", "final", "error", "close", "done",
    ]);
    for (const e of eventos) {
      expect(tiposValidos.has(e.type)).toBe(true);
    }
  });
});

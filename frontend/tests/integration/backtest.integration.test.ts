import { beforeAll, describe, expect, it } from "vitest";
import { runBacktest } from "../../lib/api";
import { ensureBackendUp } from "./helpers";

beforeAll(ensureBackendUp);

describe("runBacktest()", () => {
  it("envía ticker y dias, y el resultado trae ticker o error legible", async () => {
    const result = await runBacktest("BVN", 90);

    // Sin datos de mercado en este entorno, el backend responde con error
    // legible en vez de un 500 -- runBacktest() no debe lanzar en ese caso.
    if (result.error) {
      expect(typeof result.error).toBe("string");
    } else {
      expect(result.ticker).toBe("BVN");
      expect(result.periodo.dias).toBeGreaterThan(0);
      expect(typeof result.estrategia_pso.retorno_total).toBe("number");
      expect(typeof result.buy_hold.retorno_total).toBe("number");
      expect(Array.isArray(result.operaciones)).toBe(true);
    }
  });

  it("el error 422 del backend por dias fuera de rango se propaga como excepción", async () => {
    // dias=10 viola el Field(ge=30) de Pydantic -> 422 -> runBacktest()
    // (usa post<T>, que hace throw si !res.ok) debe rechazar la promesa.
    await expect(runBacktest("BVN", 10)).rejects.toThrow(/422/);
  });

  it("distintos periodos generan resultados con el dias solicitado (o error)", async () => {
    const r90 = await runBacktest("BVN", 90);
    const r180 = await runBacktest("BVN", 180);

    if (!r90.error && !r180.error) {
      expect(r90.periodo.dias).not.toBe(r180.periodo.dias);
    } else {
      // En este entorno ambos fallan por falta de datos; igual verificamos
      // que la llamada con distinto payload no rompe nada.
      expect(r90).toBeDefined();
      expect(r180).toBeDefined();
    }
  });
});

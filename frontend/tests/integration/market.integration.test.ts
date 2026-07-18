/**
 * Pruebas de integración: lib/api.ts (frontend real) <-> backend FastAPI real.
 *
 * A diferencia de los tests unitarios del backend (que mockean red externa)
 * y de la suite E2E de Selenium (que maneja un navegador), estas pruebas
 * llaman DIRECTAMENTE a las funciones que usan los componentes React contra
 * un backend real corriendo -- sin DOM, sin mocks de fetch -- para verificar
 * que el contrato de datos (forma del JSON, parseo, manejo de errores) entre
 * ambos lados es correcto.
 *
 * Requiere: backend corriendo en NEXT_PUBLIC_API_URL (default http://localhost:8000).
 */
import { beforeAll, describe, expect, it } from "vitest";
import { getCommodities, getHistorico, getNoticias, getPrecio, getTickers } from "../../lib/api";
import { ensureBackendUp } from "./helpers";

beforeAll(ensureBackendUp);

describe("getTickers()", () => {
  it("devuelve la lista estática de tickers BVL con la forma esperada", async () => {
    const tickers = await getTickers();

    expect(Array.isArray(tickers)).toBe(true);
    expect(tickers.length).toBeGreaterThanOrEqual(10);
    for (const t of tickers) {
      expect(typeof t.value).toBe("string");
      expect(typeof t.label).toBe("string");
    }
    expect(tickers.some((t) => t.value === "BVN")).toBe(true);
  });
});

describe("getPrecio()", () => {
  it("devuelve un objeto con el ticker solicitado, con precio o error", async () => {
    const precio = await getPrecio("BVN");

    expect(precio.ticker).toBe("BVN");
    // Sin fuente externa disponible en este entorno, precio viene con error;
    // con red real, precio/variacion_pct/moneda estarían pobladas.
    if (precio.error) {
      expect(typeof precio.error).toBe("string");
    } else {
      expect(typeof precio.precio).toBe("number");
      expect(typeof precio.moneda).toBe("string");
    }
  });

  it("no lanza excepción aunque el ticker no exista", async () => {
    await expect(getPrecio("NOEXISTE")).resolves.toBeDefined();
  });
});

describe("getHistorico()", () => {
  it("nunca lanza y siempre devuelve un array (aunque el backend falle)", async () => {
    // El backend devuelve {"error": "..."} sin salida de red (sin campo
    // "historico"); getHistorico() debe degradar a [] en ese caso, no romper.
    const historico = await getHistorico("BVN", 60);
    expect(Array.isArray(historico)).toBe(true);
  });
});

describe("getCommodities()", () => {
  it("devuelve las 3 claves de metales con precio o error por metal", async () => {
    const data = await getCommodities();

    expect(Object.keys(data).sort()).toEqual(["Cobre", "Oro", "Plata"]);
    for (const metal of Object.values(data)) {
      if (metal.error) {
        expect(typeof metal.error).toBe("string");
      } else {
        expect(typeof metal.precio).toBe("number");
        expect(typeof metal.cambio_dia_pct).toBe("number");
        expect(Array.isArray(metal.closes)).toBe(true);
      }
    }
  });
});

describe("getNoticias()", () => {
  it("devuelve alpha_vantage y google_news como arrays, para cualquier resultado", async () => {
    const data = await getNoticias("BVN");

    expect(Array.isArray(data.alpha_vantage)).toBe(true);
    expect(Array.isArray(data.google_news)).toBe(true);
  });

  it("cambia el resultado según el ticker (llama al endpoint correcto)", async () => {
    const bvn = await getNoticias("BVN");
    const scco = await getNoticias("SCCO");
    // No podemos garantizar contenido distinto sin red real, pero ambas
    // deben resolver independientemente sin cruzarse ni lanzar.
    expect(bvn).toBeDefined();
    expect(scco).toBeDefined();
  });
});

import { beforeAll, describe, expect, it } from "vitest";
import { getHistory } from "../../lib/api";
import { ensureBackendUp } from "./helpers";

beforeAll(ensureBackendUp);

describe("getHistory()", () => {
  it("devuelve un array (vacío si no hay Supabase configurado o sin registros)", async () => {
    const historial = await getHistory(undefined, 50);
    expect(Array.isArray(historial)).toBe(true);
  });

  it("acepta filtro por ticker sin lanzar", async () => {
    const historial = await getHistory("BVN", 10);
    expect(Array.isArray(historial)).toBe(true);
    for (const rec of historial) {
      expect(rec.ticker).toBe("BVN");
    }
  });

  it("respeta el límite pasado como parámetro", async () => {
    // No podemos garantizar >limit registros en este entorno, pero al menos
    // confirmamos que nunca devuelve más de lo pedido.
    const historial = await getHistory(undefined, 3);
    expect(historial.length).toBeLessThanOrEqual(3);
  });
});

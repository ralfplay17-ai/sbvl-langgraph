/**
 * Prueba de integración del manejo de errores HTTP: los helpers get<T>/post<T>
 * de lib/api.ts (privados al módulo) lanzan `Error(`${status} ${statusText}`)`
 * cuando el backend responde con un código != 2xx. Se verifica contra
 * respuestas 422 reales de FastAPI/Pydantic, no simuladas.
 */
import { beforeAll, describe, expect, it } from "vitest";
import { getHistory, runBacktest } from "../../lib/api";
import { ensureBackendUp, API_URL } from "./helpers";

beforeAll(ensureBackendUp);

describe("Manejo de errores HTTP reales del backend", () => {
  it("getHistory con limit fuera de rango (Pydantic ge=1) lanza con el código 422", async () => {
    await expect(getHistory(undefined, 0)).rejects.toThrow(/422/);
  });

  it("runBacktest con dias fuera de rango lanza con el código 422", async () => {
    await expect(runBacktest("BVN", 5000)).rejects.toThrow(/422/);
  });

  it("un endpoint inexistente responde 404 y no cuelga la petición", async () => {
    const res = await fetch(`${API_URL}/api/no-existe`);
    expect(res.status).toBe(404);
  });
});

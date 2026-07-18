export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Verifica que el backend real esté arriba antes de correr las pruebas de
 * integración. Estas pruebas NO mockean fetch: llaman a las funciones reales
 * de lib/api.ts contra un backend FastAPI real corriendo en API_URL.
 */
export async function ensureBackendUp(): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(3000) });
  } catch (err) {
    throw new Error(
      `No se pudo conectar al backend en ${API_URL}. ` +
      `Arrancalo con: cd backend && uvicorn main:app --port 8000\n` +
      `Detalle: ${(err as Error).message}`
    );
  }
  if (!res.ok) {
    throw new Error(`El backend respondió ${res.status} en /health -- no está saludable`);
  }
}

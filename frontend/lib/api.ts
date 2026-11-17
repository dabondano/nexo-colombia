/**
 * Server-side access to the NEXO API.
 * The base URL is read at request time so one build runs in any environment.
 */

export type SyncRun = {
  id: string;
  mode: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  rows_seen: number;
  rows_new: number;
  rows_changed: number;
  rows_rejected: number;
};

export type Source = {
  id: string;
  external_ref: string;
  name: string;
  institution: string;
  url: string;
  category: string;
  acquisition_method: string;
  update_frequency: string | null;
  reliability_class: number;
  licence: string | null;
  known_limitations: string | null;
  verification_status: string;
  last_verified_at: string | null;
  last_successful_sync: SyncRun | null;
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; reason: string };

function apiBaseUrl(): string {
  return process.env.NEXO_API_URL ?? "http://localhost:8000";
}

export async function fetchSources(): Promise<ApiResult<Source[]>> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/sources`, {
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) {
      return { ok: false, reason: `La API respondió con el código ${response.status}.` };
    }
    return { ok: true, data: (await response.json()) as Source[] };
  } catch {
    return { ok: false, reason: "No fue posible conectar con la API de NEXO." };
  }
}

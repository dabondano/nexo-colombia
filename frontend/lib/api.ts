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

export type Provenance = {
  source_id: string;
  source_name: string;
  source_institution: string;
  source_url: string;
  original_url: string | null;
  licence: string | null;
  reliability_class: number;
  source_verification_status: string;
  extraction_method: string;
  acquired_at: string;
  published_at: string | null;
  last_verified_at: string | null;
  /** Repairs NEXO made to the item as published. Empty for most records. */
  processing_notes: string[];
};

export type Page<T> = { total: number; limit: number; offset: number; items: T[] };

export type FilterOption = { value: string; count: number };

export type InstitutionSummary = {
  id: string;
  official_code: string;
  name: string;
  order: string | null;
  suborder: string | null;
  organic_classification: string | null;
  sector: string | null;
  legal_nature: string | null;
  department: string | null;
  municipality: string | null;
  data_quality_status: string;
};

export type Institution = InstitutionSummary & {
  nit: string | null;
  level: string | null;
  institution_type: string | null;
  website: string | null;
  longitude: number | null;
  latitude: number | null;
  status: string | null;
  jurisdiction_code: string;
  epistemic_label: string;
  provenance: Provenance;
};

export type InstitutionFilters = {
  order: FilterOption[];
  organic_classification: FilterOption[];
  sector: FilterOption[];
  department: FilterOption[];
};

export type InitiativeSummary = {
  id: string;
  camara_number: string | null;
  senado_number: string | null;
  short_title: string | null;
  title: string;
  law_type: string | null;
  status: string | null;
  origin_chamber: string | null;
  commission: string | null;
  legislature: string | null;
  camara_filed_on: string | null;
  data_quality_status: string;
};

export type Initiative = InitiativeSummary & {
  senado_filed_on: string | null;
  purpose: string | null;
  observations: string | null;
  authors_text: string | null;
  jurisdiction_code: string;
  epistemic_label: string;
  provenance: Provenance;
};

export type InitiativeFilters = {
  legislature: FilterOption[];
  law_type: FilterOption[];
  status: FilterOption[];
  commission: FilterOption[];
  origin_chamber: FilterOption[];
};

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; reason: string; notFound: boolean };

type Params = Record<string, string | number | undefined>;

function apiBaseUrl(): string {
  return process.env.NEXO_API_URL ?? "http://localhost:8000";
}

async function getJson<T>(path: string, params: Params = {}): Promise<ApiResult<T>> {
  const url = new URL(`/api/v1${path}`, apiBaseUrl());
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
    if (!response.ok) {
      return {
        ok: false,
        reason: `La API respondió con el código ${response.status}.`,
        notFound: response.status === 404 || response.status === 422,
      };
    }
    return { ok: true, data: (await response.json()) as T };
  } catch {
    return { ok: false, reason: "No fue posible conectar con la API de NEXO.", notFound: false };
  }
}

export const fetchSources = () => getJson<Source[]>("/sources");

export const fetchInstitutions = (params: Params) =>
  getJson<Page<InstitutionSummary>>("/institutions", params);
export const fetchInstitutionFilters = () => getJson<InstitutionFilters>("/institutions/filters");
export const fetchInstitution = (id: string) =>
  getJson<Institution>(`/institutions/${encodeURIComponent(id)}`);

export const fetchInitiatives = (params: Params) =>
  getJson<Page<InitiativeSummary>>("/initiatives", params);
export const fetchInitiativeFilters = () => getJson<InitiativeFilters>("/initiatives/filters");
export const fetchInitiative = (id: string) =>
  getJson<Initiative>(`/initiatives/${encodeURIComponent(id)}`);

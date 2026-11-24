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
  linked_authors: LinkedAuthor[];
  linked_authors_label: string;
  linked_authors_rule: string;
  jurisdiction_code: string;
  epistemic_label: string;
  provenance: Provenance;
};

export type LinkedAuthor = {
  representative_id: string;
  full_name: string;
  author_name: string;
};

export type RepresentativeSummary = {
  id: string;
  person_id: string;
  full_name: string;
  position: string;
  corporation: string;
  period: string;
  constituency: string | null;
  party: string | null;
  seat_basis: string | null;
  data_quality_status: string;
};

export type AuthoredInitiative = {
  id: string;
  title: string;
  camara_number: string | null;
  senado_number: string | null;
  legislature: string | null;
  status: string | null;
  author_name: string;
};

export type Representative = RepresentativeSummary & {
  email: string | null;
  office: string | null;
  phone: string | null;
  jurisdiction_code: string;
  epistemic_label: string;
  provenance: Provenance;
  authored_initiatives: AuthoredInitiative[];
  authored_initiatives_label: string;
  authored_initiatives_rule: string;
};

export type RepresentativeFilters = {
  constituency: FilterOption[];
  party: FilterOption[];
};

export type InitiativeFilters = {
  legislature: FilterOption[];
  law_type: FilterOption[];
  status: FilterOption[];
  commission: FilterOption[];
  origin_chamber: FilterOption[];
};

export type InstrumentSummary = {
  id: string;
  slug: string;
  title: string;
  instrument_type: string;
  year: number | null;
  /** What is known about how current the loaded edition is. */
  edition_note: string | null;
};

export type OutlineItem = {
  id: string;
  parent_id: string | null;
  path: string;
  kind: "preambulo" | "titulo" | "capitulo" | "articulo";
  label: string;
  heading: string | null;
  excerpt: string | null;
  data_quality_status: string;
};

export type Instrument = InstrumentSummary & {
  article_count: number;
  articles_needing_review: number;
  outline: OutlineItem[];
  provenance: Provenance;
};

export type ProvisionRef = { id: string; path: string; label: string; heading: string | null };

/**
 * "text": wording. "note": editor's note. "after_previous_mark": wording the
 * source prints after its mark "TEXTO ANTERIOR", which may not be in force.
 */
export type Segment = { kind: "text" | "note" | "after_previous_mark"; text: string };

export type Provision = {
  id: string;
  path: string;
  kind: OutlineItem["kind"];
  label: string;
  heading: string | null;
  data_quality_status: string;
  instrument: InstrumentSummary;
  ancestors: ProvisionRef[];
  segments: Segment[];
  recorded_at: string | null;
  previous: ProvisionRef | null;
  next: ProvisionRef | null;
  provenance: Provenance;
};

export type RecordType =
  | "legal_provision"
  | "legislative_initiative"
  | "representative"
  | "institution";

export type SearchHit = {
  record_type: RecordType;
  record_id: string;
  title: string;
  summary: string | null;
  record_date: string | null;
};

export type SearchPage = {
  query: string;
  total: number;
  limit: number;
  offset: number;
  counts: { record_type: RecordType; count: number }[];
  items: SearchHit[];
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

/**
 * Asks the API whether a record exists, without loading it (HTTP HEAD).
 * Returns false only when the API says the record does not exist (404, or 422 for a
 * malformed identifier); any other answer or a connection failure returns true, so the
 * page still renders and explains the problem itself.
 */
export async function recordExists(path: string): Promise<boolean> {
  try {
    const response = await fetch(new URL(`/api/v1${path}`, apiBaseUrl()), {
      method: "HEAD",
      signal: AbortSignal.timeout(2000),
    });
    return !(response.status === 404 || response.status === 422);
  } catch {
    return true;
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

export const fetchRepresentatives = (params: Params) =>
  getJson<Page<RepresentativeSummary>>("/representatives", params);
export const fetchRepresentativeFilters = () =>
  getJson<RepresentativeFilters>("/representatives/filters");
export const representativePath = (id: string) => `/representatives/${encodeURIComponent(id)}`;
export const fetchRepresentative = (id: string) => getJson<Representative>(representativePath(id));

export const CONSTITUTION_SLUG = "constitucion-politica-1991";
export const fetchInstrument = (slug: string) =>
  getJson<Instrument>(`/instruments/${encodeURIComponent(slug)}`);

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * A provision of the Constitution by its stable key ("articulo-11"), or by its
 * record id, which search results use.
 */
export const constitutionProvisionPath = (key: string) =>
  UUID.test(key)
    ? `/provisions/${encodeURIComponent(key)}`
    : `/instruments/${CONSTITUTION_SLUG}/provisions/${encodeURIComponent(key)}`;
export const fetchConstitutionProvision = (key: string) =>
  getJson<Provision>(constitutionProvisionPath(key));

export const fetchSearch = (params: Params) => getJson<SearchPage>("/search", params);

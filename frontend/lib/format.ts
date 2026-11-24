/** Formatting and vocabulary shared by record pages. */

const longDate = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "long",
  timeZone: "America/Bogota",
});

// Calendar dates (no time of day) must not shift when converted to a time zone.
const calendarDate = new Intl.DateTimeFormat("es-CO", { dateStyle: "long", timeZone: "UTC" });

const numberFormat = new Intl.NumberFormat("es-CO");

export function formatDateTime(value: string | null): string {
  return value ? longDate.format(new Date(value)) : "Sin registro";
}

export function formatCalendarDate(value: string | null): string {
  return value ? calendarDate.format(new Date(`${value}T00:00:00Z`)) : "Sin registro";
}

export function formatNumber(value: number): string {
  return numberFormat.format(value);
}

/** Epistemic Labels (master brief, section 2.1). */
export const EPISTEMIC_LABELS: Record<string, { name: string; meaning: string }> = {
  hecho_documentado: {
    name: "Hecho documentado",
    meaning: "Dato tomado directamente de una fuente oficial que se puede consultar.",
  },
  interpretacion_juridica: {
    name: "Interpretación jurídica",
    meaning: "Lectura de una norma o decisión; puede haber otras interpretaciones.",
  },
  hipotesis_analitica: {
    name: "Hipótesis analítica",
    meaning: "Inferencia a partir de datos; no es un hecho comprobado.",
  },
  simulacion_hipotetica: {
    name: "Simulación hipotética",
    meaning: "Escenario supuesto; no describe hechos ocurridos.",
  },
  no_verificado: {
    name: "No verificado",
    meaning: "Información que aún no se ha contrastado con una fuente.",
  },
};

/** Data-quality status describes the record, never the entity or person it is about. */
export const QUALITY_LABELS: Record<string, { name: string; meaning: string }> = {
  verified: {
    name: "Verificado",
    meaning: "El registro fue contrastado con una segunda fuente oficial.",
  },
  acceptable: {
    name: "Aceptable",
    meaning: "El registro tiene los campos principales, según lo publica la fuente.",
  },
  incomplete: {
    name: "Incompleto",
    meaning: "A la fuente le faltan campos principales de este registro.",
  },
  conflicting: {
    name: "Con diferencias",
    meaning: "Dos fuentes oficiales no coinciden sobre este registro.",
  },
  stale: {
    name: "Desactualizado",
    meaning: "La fuente no se actualiza desde hace tiempo.",
  },
};

export type SearchParams = Record<string, string | string[] | undefined>;

/** First value of a query-string parameter, trimmed; undefined when absent or empty. */
export function param(searchParams: SearchParams, key: string): string | undefined {
  const raw = searchParams[key];
  const value = (Array.isArray(raw) ? raw[0] : raw)?.trim();
  return value ? value : undefined;
}

export function pageNumber(searchParams: SearchParams): number {
  const page = Number.parseInt(param(searchParams, "pagina") ?? "1", 10);
  return Number.isFinite(page) && page >= 1 ? page : 1;
}

const pesos = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
const oneDecimal = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1, minimumFractionDigits: 1 });

/** Full amount in pesos, as published: "$ 7.548.345.900". */
export function formatPesos(value: string): string {
  return `$ ${pesos.format(Number(value))}`;
}

/** Rounded amount in Colombian usage (billón = un millón de millones). */
export function formatPesosShort(value: string): string {
  const amount = Number(value);
  if (amount >= 1e12) return `$ ${oneDecimal.format(amount / 1e12)} billones`;
  if (amount >= 1e9) return `$ ${oneDecimal.format(amount / 1e9)} mil millones`;
  if (amount >= 1e6) return `$ ${oneDecimal.format(amount / 1e6)} millones`;
  return formatPesos(value);
}

/** A share between 0 and 1 as a percentage; "No aplica" when there is no appropriation. */
export function formatRate(value: string | null): string {
  return value === null ? "No aplica" : `${oneDecimal.format(Number(value) * 100)} %`;
}

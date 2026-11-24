import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import { fetchSearch, type RecordType, type SearchHit } from "@/lib/api";
import {
  formatCalendarDate,
  formatNumber,
  pageNumber,
  param,
  type SearchParams,
} from "@/lib/format";

export const metadata: Metadata = {
  title: "Buscar",
  description:
    "Búsqueda en la Constitución, los proyectos de ley, los representantes, las entidades públicas y su presupuesto cargados en NEXO Colombia.",
};

const PAGE_SIZE = 25;
const BASE_PATH = "/buscar";

const TYPES: Record<RecordType, { singular: string; plural: string; path: string }> = {
  legal_provision: {
    singular: "Artículo de la Constitución",
    plural: "Artículos de la Constitución",
    path: "/constitucion",
  },
  legislative_initiative: {
    singular: "Iniciativa legislativa",
    plural: "Iniciativas legislativas",
    path: "/legislacion",
  },
  representative: {
    singular: "Representante a la Cámara",
    plural: "Representantes a la Cámara",
    path: "/representantes",
  },
  institution: { singular: "Entidad pública", plural: "Entidades públicas", path: "/instituciones" },
  budget_entity: {
    singular: "Presupuesto de una entidad",
    plural: "Presupuesto de entidades",
    path: "/presupuesto",
  },
};

function isRecordType(value: string | undefined): value is RecordType {
  return value !== undefined && value in TYPES;
}

function href(q: string, type?: RecordType): string {
  const params = new URLSearchParams({ q });
  if (type) params.set("tipo", type);
  return `${BASE_PATH}?${params.toString()}`;
}

function Hit({ hit }: { hit: SearchHit }) {
  const type = TYPES[hit.record_type];
  return (
    <li className="border-t border-rule py-4 first:border-t-0">
      <p className="text-sm font-medium uppercase tracking-wide text-accent">
        {type.singular}
        {hit.record_date ? (
          <span className="normal-case tracking-normal text-ink-muted">
            {" "}
            · Radicada el {formatCalendarDate(hit.record_date)}
          </span>
        ) : null}
      </p>
      <h3 className="mt-1 text-lg font-semibold">
        <Link
          href={`${type.path}/${encodeURIComponent(hit.record_key)}`}
          className="text-brand underline underline-offset-4"
        >
          {hit.title}
        </Link>
      </h3>
      {hit.summary ? <p className="mt-1 line-clamp-3 text-ink-muted">{hit.summary}</p> : null}
    </li>
  );
}

function TypeTabs(props: {
  q: string;
  selected: RecordType | undefined;
  counts: { record_type: RecordType; count: number }[];
}) {
  const all = props.counts.reduce((sum, item) => sum + item.count, 0);
  const options: { type: RecordType | undefined; label: string; count: number }[] = [
    { type: undefined, label: "Todo", count: all },
    ...props.counts.map((item) => ({
      type: item.record_type,
      label: TYPES[item.record_type].plural,
      count: item.count,
    })),
  ];
  return (
    <nav aria-label="Tipo de registro">
      <ul className="flex flex-wrap gap-2">
        {options.map((option) => {
          const current = option.type === props.selected;
          return (
            <li key={option.type ?? "todo"}>
              <Link
                href={href(props.q, option.type)}
                aria-current={current ? "page" : undefined}
                className={
                  current
                    ? "inline-block rounded border border-brand bg-brand px-4 py-2 text-brand-ink"
                    : "inline-block rounded border border-rule bg-surface px-4 py-2 text-brand hover:underline"
                }
              >
                {option.label} ({formatNumber(option.count)})
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

function SearchForm({ q }: { q: string | undefined }) {
  return (
    <form
      action={BASE_PATH}
      method="get"
      role="search"
      aria-label="Buscar en todos los registros"
      className="flex flex-wrap items-end gap-3 rounded border border-rule bg-surface p-5"
    >
      <div className="flex min-w-0 flex-1 basis-64 flex-col gap-1">
        <label htmlFor="busqueda" className="text-sm font-medium">
          Palabras, número de artículo, número de proyecto o NIT
        </label>
        <input
          id="busqueda"
          name="q"
          type="search"
          required
          maxLength={200}
          defaultValue={q ?? ""}
          placeholder="Por ejemplo: salud mental, artículo 86, 217/2026C, alcaldía de Tunja"
          className="w-full rounded border border-rule bg-surface px-3 py-2 text-base text-ink"
        />
      </div>
      <button
        type="submit"
        className="rounded bg-brand px-5 py-2 font-medium text-brand-ink hover:opacity-90"
      >
        Buscar
      </button>
    </form>
  );
}

function HowItWorks() {
  return (
    <p className="max-w-3xl text-sm text-ink-muted">
      La búsqueda exige todas las palabras escritas, sin distinguir mayúsculas, tildes ni
      plurales. Use comillas para una frase exacta y un guion delante de una palabra para
      excluirla. No reconoce sinónimos. Los resultados se ordenan únicamente por la coincidencia
      con el texto buscado: primero los registros cuyo nombre contiene todas las palabras, y
      luego pesa más el nombre o el número del registro que el resto de su contenido. En la
      Constitución solo se busca en el texto que la fuente presenta como vigente, no en sus
      notas ni en textos anteriores.
    </p>
  );
}

async function Results({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const query = await searchParams;
  const q = param(query, "q");
  const rawType = param(query, "tipo");
  const type = isRecordType(rawType) ? rawType : undefined;
  const page = pageNumber(query);

  if (!q) {
    return (
      <>
        <SearchForm q={undefined} />
        <Notice>
          Escriba una o varias palabras para buscar en la Constitución, en los proyectos de ley
          y los representantes de la Cámara, en el directorio de entidades públicas y en el
          presupuesto de las entidades nacionales.
        </Notice>
        <HowItWorks />
      </>
    );
  }

  const result = await fetchSearch({
    q,
    type,
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
  });

  if (!result.ok) {
    return (
      <>
        <SearchForm q={q} />
        <Notice>{result.reason} La búsqueda no está disponible en este momento.</Notice>
      </>
    );
  }

  const { total, items, counts } = result.data;
  const anyMatch = counts.length > 0;
  const first = (page - 1) * PAGE_SIZE + 1;

  return (
    <>
      <SearchForm q={q} />
      <section aria-labelledby="titulo-resultados" className="flex flex-col gap-4">
        <h2 id="titulo-resultados" className="text-xl font-semibold" role="status">
          {total === 0
            ? "Sin resultados"
            : `${formatNumber(total)} ${total === 1 ? "resultado" : "resultados"}`}{" "}
          para «{q}»
          {total > PAGE_SIZE && items.length > 0 ? (
            <span className="text-base font-normal text-ink-muted">
              {" "}
              (se muestran del {formatNumber(first)} al {formatNumber(first + items.length - 1)})
            </span>
          ) : null}
        </h2>
        {anyMatch ? <TypeTabs q={q} selected={type} counts={counts} /> : null}
        {!anyMatch ? (
          <Notice>
            Ningún registro cargado contiene todas esas palabras. Puede probar con menos palabras
            o con otra forma de escribirlas. NEXO solo busca en los datos ya cargados: los
            proyectos de ley publicados por la Cámara de Representantes y el directorio de
            entidades públicas.
          </Notice>
        ) : items.length === 0 ? (
          <Notice>Esta página de resultados no existe.</Notice>
        ) : (
          <ul className="rounded border border-rule bg-surface px-5">
            {items.map((hit) => (
              <Hit key={`${hit.record_type}-${hit.record_id}`} hit={hit} />
            ))}
          </ul>
        )}
        <Pagination
          basePath={BASE_PATH}
          query={{ q, tipo: type }}
          page={page}
          pageSize={PAGE_SIZE}
          total={total}
        />
      </section>
      <HowItWorks />
    </>
  );
}

export default function BuscarPage(props: PageProps<"/buscar">) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="font-serif text-3xl font-semibold text-brand">Buscar</h1>
      <Suspense fallback={<p role="status">Buscando…</p>}>
        <Results searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

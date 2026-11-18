import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { FilterForm, SelectFilter, TextFilter } from "@/components/Filters";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import {
  fetchRepresentativeFilters,
  fetchRepresentatives,
  type RepresentativeSummary,
} from "@/lib/api";
import { formatNumber, pageNumber, param, type SearchParams } from "@/lib/format";

export const metadata: Metadata = {
  title: "Representantes",
  description:
    "Representantes a la Cámara del período 2026-2027, con la fuente de cada registro.",
};

const PAGE_SIZE = 25;
const BASE_PATH = "/representantes";

function RepresentativeItem({ item }: { item: RepresentativeSummary }) {
  const details = [
    item.constituency,
    item.party ?? (item.seat_basis ? "Curul de la oposición" : null),
  ].filter(Boolean);
  return (
    <li className="border-t border-rule py-4 first:border-t-0">
      <h3 className="text-lg font-semibold">
        <Link href={`${BASE_PATH}/${item.id}`} className="text-brand underline underline-offset-4">
          {item.full_name}
        </Link>
      </h3>
      {details.length > 0 ? <p className="mt-1 text-ink-muted">{details.join(" · ")}</p> : null}
    </li>
  );
}

async function Directory({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const query = await searchParams;
  const filters = {
    q: param(query, "q"),
    circunscripcion: param(query, "circunscripcion"),
    partido: param(query, "partido"),
  };
  const page = pageNumber(query);
  const hasFilters = Object.values(filters).some(Boolean);

  const [options, result] = await Promise.all([
    fetchRepresentativeFilters(),
    fetchRepresentatives({
      q: filters.q,
      constituency: filters.circunscripcion,
      party: filters.partido,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    }),
  ]);

  if (!result.ok || !options.ok) {
    const reason = !result.ok ? result.reason : !options.ok ? options.reason : "";
    return (
      <Notice>{reason} El directorio de representantes no está disponible en este momento.</Notice>
    );
  }

  const { total, items } = result.data;
  const first = (page - 1) * PAGE_SIZE + 1;

  return (
    <div className="flex flex-col gap-6">
      <FilterForm action={BASE_PATH} legend="Buscar representantes" hasFilters={hasFilters}>
        <TextFilter
          name="q"
          label="Nombre"
          value={filters.q}
          placeholder="Por ejemplo: maría"
        />
        <SelectFilter
          name="circunscripcion"
          label="Circunscripción"
          value={filters.circunscripcion}
          options={options.data.constituency}
        />
        <SelectFilter
          name="partido"
          label="Partido, movimiento u organización"
          value={filters.partido}
          options={options.data.party}
        />
      </FilterForm>

      <section aria-labelledby="titulo-resultados" className="flex flex-col gap-4">
        <h2 id="titulo-resultados" className="text-xl font-semibold" role="status">
          {total === 0
            ? "Sin resultados"
            : `${formatNumber(total)} ${total === 1 ? "representante" : "representantes"}`}
          {total > PAGE_SIZE && items.length > 0 ? (
            <span className="text-base font-normal text-ink-muted">
              {" "}
              (se muestran del {formatNumber(first)} al{" "}
              {formatNumber(first + items.length - 1)}, en orden alfabético)
            </span>
          ) : null}
        </h2>
        {total === 0 ? (
          <Notice>
            {hasFilters
              ? "Ningún representante coincide con esta búsqueda. Puede probar con menos palabras o quitar filtros."
              : "Todavía no se han cargado representantes en la plataforma."}
          </Notice>
        ) : items.length === 0 ? (
          <Notice>Esta página de resultados no existe.</Notice>
        ) : (
          <ul className="rounded border border-rule bg-surface px-5">
            {items.map((item) => (
              <RepresentativeItem key={item.id} item={item} />
            ))}
          </ul>
        )}
        <Pagination
          basePath={BASE_PATH}
          query={filters}
          page={page}
          pageSize={PAGE_SIZE}
          total={total}
        />
      </section>
    </div>
  );
}

export default function RepresentantesPage(props: PageProps<"/representantes">) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="font-serif text-3xl font-semibold text-brand">Representantes a la Cámara</h1>
      <p className="max-w-3xl text-ink-muted">
        Integrantes de la Cámara de Representantes según el conjunto de datos «Representantes
        período 2026-2027» que publica la propia Cámara. La fuente no incluye comisiones ni
        fechas de posesión. Cada ficha enlaza al origen de su registro y explica cómo NEXO
        corrigió el orden de las columnas de la fuente.
      </p>
      <Suspense fallback={<p role="status">Cargando el directorio de representantes…</p>}>
        <Directory searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

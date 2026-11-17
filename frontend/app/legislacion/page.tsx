import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { FilterForm, SelectFilter, TextFilter } from "@/components/Filters";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import { fetchInitiativeFilters, fetchInitiatives, type InitiativeSummary } from "@/lib/api";
import { formatNumber, pageNumber, param, type SearchParams } from "@/lib/format";

export const metadata: Metadata = {
  title: "Legislación",
  description:
    "Proyectos de ley y de acto legislativo publicados por la Cámara de Representantes, con la fuente de cada registro.",
};

const PAGE_SIZE = 25;
const BASE_PATH = "/legislacion";

function numbers(item: InitiativeSummary): string | null {
  const parts = [
    item.camara_number ? `Cámara ${item.camara_number}` : null,
    item.senado_number ? `Senado ${item.senado_number}` : null,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : null;
}

function InitiativeItem({ item }: { item: InitiativeSummary }) {
  const details = [
    numbers(item),
    item.law_type,
    item.legislature ? `Legislatura ${item.legislature}` : null,
  ].filter(Boolean);
  return (
    <li className="border-t border-rule py-4 first:border-t-0">
      <h3 className="text-lg font-semibold">
        <Link href={`${BASE_PATH}/${item.id}`} className="text-brand underline underline-offset-4">
          {item.short_title ?? item.title}
        </Link>
      </h3>
      {item.short_title ? <p className="mt-1">{item.title}</p> : null}
      <p className="mt-1 text-ink-muted">{details.join(" · ")}</p>
      {item.status ? (
        <p className="mt-1 text-sm">
          <span className="text-ink-muted">Estado según la fuente: </span>
          <span className="font-medium">{item.status}</span>
        </p>
      ) : null}
    </li>
  );
}

async function InitiativeList({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const query = await searchParams;
  const filters = {
    q: param(query, "q"),
    autor: param(query, "autor"),
    legislatura: param(query, "legislatura"),
    tipo: param(query, "tipo"),
    estado: param(query, "estado"),
    comision: param(query, "comision"),
    origen: param(query, "origen"),
  };
  const page = pageNumber(query);
  const hasFilters = Object.values(filters).some(Boolean);

  const [options, result] = await Promise.all([
    fetchInitiativeFilters(),
    fetchInitiatives({
      q: filters.q,
      author: filters.autor,
      legislature: filters.legislatura,
      law_type: filters.tipo,
      status: filters.estado,
      commission: filters.comision,
      origin_chamber: filters.origen,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    }),
  ]);

  if (!result.ok || !options.ok) {
    const reason = !result.ok ? result.reason : !options.ok ? options.reason : "";
    return <Notice>{reason} Los proyectos de ley no están disponibles en este momento.</Notice>;
  }

  const { total, items } = result.data;
  const first = (page - 1) * PAGE_SIZE + 1;

  return (
    <div className="flex flex-col gap-6">
      <FilterForm action={BASE_PATH} legend="Buscar proyectos de ley" hasFilters={hasFilters}>
        <TextFilter
          name="q"
          label="Palabras del título"
          value={filters.q}
          placeholder="Por ejemplo: educación rural"
        />
        <TextFilter
          name="autor"
          label="Autor (texto de la fuente)"
          value={filters.autor}
          placeholder="Nombre o apellido"
        />
        <SelectFilter
          name="legislatura"
          label="Legislatura"
          value={filters.legislatura}
          options={options.data.legislature}
        />
        <SelectFilter
          name="tipo"
          label="Tipo de iniciativa"
          value={filters.tipo}
          options={options.data.law_type}
        />
        <SelectFilter
          name="estado"
          label="Estado según la fuente"
          value={filters.estado}
          options={options.data.status}
        />
        <SelectFilter
          name="comision"
          label="Comisión"
          value={filters.comision}
          options={options.data.commission}
        />
        <SelectFilter
          name="origen"
          label="Cámara de origen"
          value={filters.origen}
          options={options.data.origin_chamber}
        />
      </FilterForm>

      <section aria-labelledby="titulo-resultados" className="flex flex-col gap-4">
        <h2 id="titulo-resultados" className="text-xl font-semibold" role="status">
          {total === 0
            ? "Sin resultados"
            : `${formatNumber(total)} ${total === 1 ? "iniciativa" : "iniciativas"}`}
          {total > PAGE_SIZE && items.length > 0 ? (
            <span className="text-base font-normal text-ink-muted">
              {" "}
              (se muestran de la {formatNumber(first)} a la{" "}
              {formatNumber(first + items.length - 1)}, de la legislatura más reciente a la más
              antigua)
            </span>
          ) : null}
        </h2>
        {total === 0 ? (
          <Notice>
            {hasFilters
              ? "Ninguna iniciativa coincide con esta búsqueda. Puede probar con menos palabras o quitar filtros."
              : "Todavía no se han cargado proyectos de ley en la plataforma."}
          </Notice>
        ) : items.length === 0 ? (
          <Notice>Esta página de resultados no existe.</Notice>
        ) : (
          <ul className="rounded border border-rule bg-surface px-5">
            {items.map((item) => (
              <InitiativeItem key={item.id} item={item} />
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

export default function LegislacionPage(props: PageProps<"/legislacion">) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="font-serif text-3xl font-semibold text-brand">Legislación</h1>
      <p className="max-w-3xl text-ink-muted">
        Proyectos de ley y de acto legislativo tomados del conjunto de datos «Proyectos de Ley»
        de la Cámara de Representantes. El estado de cada iniciativa es el que publica la fuente
        y puede no reflejar las últimas actuaciones. Este conjunto no incluye el historial de
        debates ni las votaciones, y no cubre todos los proyectos que solo se tramitan en el
        Senado.
      </p>
      <Suspense fallback={<p role="status">Cargando los proyectos de ley…</p>}>
        <InitiativeList searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

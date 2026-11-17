import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { FilterForm, SelectFilter, TextFilter } from "@/components/Filters";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import { fetchInstitutionFilters, fetchInstitutions, type InstitutionSummary } from "@/lib/api";
import { formatNumber, pageNumber, param, type SearchParams } from "@/lib/format";

export const metadata: Metadata = {
  title: "Instituciones",
  description: "Directorio de entidades públicas de Colombia, con la fuente de cada registro.",
};

const PAGE_SIZE = 25;
const BASE_PATH = "/instituciones";

function place(item: InstitutionSummary): string | null {
  const parts = [item.municipality, item.department].filter(Boolean);
  return parts.length > 0 ? parts.join(", ") : null;
}

function InstitutionItem({ item }: { item: InstitutionSummary }) {
  const details = [item.legal_nature, item.order, place(item)].filter(Boolean);
  return (
    <li className="border-t border-rule py-4 first:border-t-0">
      <h3 className="text-lg font-semibold">
        <Link href={`${BASE_PATH}/${item.id}`} className="text-brand underline underline-offset-4">
          {item.name}
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
    orden: param(query, "orden"),
    clasificacion: param(query, "clasificacion"),
    sector: param(query, "sector"),
    departamento: param(query, "departamento"),
  };
  const page = pageNumber(query);
  const hasFilters = Object.values(filters).some(Boolean);

  const [options, result] = await Promise.all([
    fetchInstitutionFilters(),
    fetchInstitutions({
      q: filters.q,
      order: filters.orden,
      organic_classification: filters.clasificacion,
      sector: filters.sector,
      department: filters.departamento,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    }),
  ]);

  if (!result.ok || !options.ok) {
    const reason = !result.ok ? result.reason : !options.ok ? options.reason : "";
    return <Notice>{reason} El directorio de entidades no está disponible en este momento.</Notice>;
  }

  const { total, items } = result.data;
  const first = (page - 1) * PAGE_SIZE + 1;

  return (
    <div className="flex flex-col gap-6">
      <FilterForm action={BASE_PATH} legend="Buscar entidades" hasFilters={hasFilters}>
        <TextFilter
          name="q"
          label="Nombre de la entidad"
          value={filters.q}
          placeholder="Por ejemplo: ministerio de salud"
        />
        <SelectFilter name="orden" label="Orden" value={filters.orden} options={options.data.order} />
        <SelectFilter
          name="clasificacion"
          label="Clasificación orgánica"
          value={filters.clasificacion}
          options={options.data.organic_classification}
        />
        <SelectFilter
          name="sector"
          label="Sector administrativo"
          value={filters.sector}
          options={options.data.sector}
        />
        <SelectFilter
          name="departamento"
          label="Departamento"
          value={filters.departamento}
          options={options.data.department}
        />
      </FilterForm>

      <section aria-labelledby="titulo-resultados" className="flex flex-col gap-4">
        <h2 id="titulo-resultados" className="text-xl font-semibold" role="status">
          {total === 0
            ? "Sin resultados"
            : `${formatNumber(total)} ${total === 1 ? "entidad" : "entidades"}`}
          {total > PAGE_SIZE && items.length > 0 ? (
            <span className="text-base font-normal text-ink-muted">
              {" "}
              (se muestran de la {formatNumber(first)} a la{" "}
              {formatNumber(first + items.length - 1)}, en orden alfabético)
            </span>
          ) : null}
        </h2>
        {total === 0 ? (
          <Notice>
            {hasFilters
              ? "Ninguna entidad del directorio coincide con esta búsqueda. Puede probar con menos palabras o quitar filtros."
              : "Todavía no se han cargado entidades en la plataforma."}
          </Notice>
        ) : items.length === 0 ? (
          <Notice>Esta página de resultados no existe.</Notice>
        ) : (
          <ul className="rounded border border-rule bg-surface px-5">
            {items.map((item) => (
              <InstitutionItem key={item.id} item={item} />
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

export default function InstitucionesPage(props: PageProps<"/instituciones">) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="font-serif text-3xl font-semibold text-brand">Instituciones</h1>
      <p className="max-w-3xl text-ink-muted">
        Directorio de entidades públicas del orden nacional y territorial, tomado del conjunto
        de datos «Universo de entidades» del Departamento Administrativo de la Función Pública.
        Los nombres se muestran tal como los publica la fuente. Cada entidad enlaza al origen
        de su registro.
      </p>
      <Suspense fallback={<p role="status">Cargando el directorio de entidades…</p>}>
        <Directory searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

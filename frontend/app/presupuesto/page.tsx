import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BudgetFigures, BudgetNotes } from "@/components/BudgetFigures";
import { FilterForm, SelectFilter, TextFilter } from "@/components/Filters";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import { ScrollRegion } from "@/components/ScrollRegion";
import { fetchBudgetEntities, fetchBudgetFilters, fetchBudgetSummary } from "@/lib/api";
import {
  formatDateTime,
  formatNumber,
  formatPesosShort,
  formatRate,
  pageNumber,
  param,
  type SearchParams,
} from "@/lib/format";

export const metadata: Metadata = {
  title: "Presupuesto",
  description:
    "Ejecución del Presupuesto General de la Nación por entidad, con la fuente de cada cifra.",
};

const PAGE_SIZE = 25;
const BASE_PATH = "/presupuesto";
const linkClass = "text-brand underline underline-offset-4";

async function Summary() {
  const result = await fetchBudgetSummary();
  if (!result.ok) {
    return <Notice>{result.reason} El resumen del presupuesto no está disponible en este momento.</Notice>;
  }
  const summary = result.data;
  if (summary.row_count === 0) {
    return <Notice>Todavía no se han cargado datos de ejecución presupuestal.</Notice>;
  }
  return (
    <section aria-labelledby="titulo-total" className="flex flex-col gap-4">
      <h2 id="titulo-total" className="text-xl font-semibold">
        Total de {formatNumber(summary.entity_count)} entidades del nivel nacional
      </h2>
      <p className="text-sm text-ink-muted">
        Última actualización de la fuente: {formatDateTime(summary.source_updated_at)}.
      </p>
      <BudgetFigures amounts={summary.amounts} rates={summary.rates} />
      <BudgetNotes yearNote={summary.year_note} formula={summary.rate_formula} />
      <details className="rounded border border-rule bg-surface p-4">
        <summary className="cursor-pointer font-medium text-brand">
          Totales por sector ({formatNumber(summary.sectors.length)}, en orden alfabético)
        </summary>
        <ScrollRegion label="Tabla por sector" className="mt-3">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Ejecución presupuestal por sector</caption>
            <thead>
              <tr className="border-b border-rule">
                <th scope="col" className="p-2">Sector</th>
                <th scope="col" className="p-2 text-right">Entidades</th>
                <th scope="col" className="p-2 text-right">Apropiación</th>
                <th scope="col" className="p-2 text-right">Comprometido</th>
                <th scope="col" className="p-2 text-right">Pagado</th>
              </tr>
            </thead>
            <tbody>
              {summary.sectors.map((sector) => (
                <tr key={sector.sector_name ?? "sin-sector"} className="border-t border-rule">
                  <th scope="row" className="p-2 font-normal">
                    {sector.sector_name ? (
                      <Link
                        href={`${BASE_PATH}?sector=${encodeURIComponent(sector.sector_name)}#titulo-entidades`}
                        className={linkClass}
                      >
                        {sector.sector_name}
                      </Link>
                    ) : (
                      "Sin sector en la fuente"
                    )}
                  </th>
                  <td className="p-2 text-right">{formatNumber(sector.entity_count)}</td>
                  <td className="p-2 text-right">{formatPesosShort(sector.amounts.appropriation)}</td>
                  <td className="p-2 text-right">{formatRate(sector.rates.commitments)}</td>
                  <td className="p-2 text-right">{formatRate(sector.rates.payments)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollRegion>
      </details>
    </section>
  );
}

async function Directory({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const query = await searchParams;
  const filters = { q: param(query, "q"), sector: param(query, "sector") };
  const page = pageNumber(query);
  const hasFilters = Object.values(filters).some(Boolean);
  const [options, result] = await Promise.all([
    fetchBudgetFilters(),
    fetchBudgetEntities({
      q: filters.q,
      sector: filters.sector,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    }),
  ]);
  if (!result.ok || !options.ok) {
    const reason = !result.ok ? result.reason : !options.ok ? options.reason : "";
    return <Notice>{reason} El directorio del presupuesto no está disponible en este momento.</Notice>;
  }
  const { total, items } = result.data;
  return (
    <section aria-labelledby="titulo-entidades" className="flex flex-col gap-4">
      <h2 id="titulo-entidades" className="text-xl font-semibold">
        Entidades
      </h2>
      <FilterForm action={BASE_PATH} legend="Buscar entidades en el presupuesto" hasFilters={hasFilters}>
        <TextFilter name="q" label="Nombre de la entidad" value={filters.q} placeholder="Por ejemplo: ideam" />
        <SelectFilter name="sector" label="Sector" value={filters.sector} options={options.data.sector} />
      </FilterForm>
      <p role="status" className="font-semibold">
        {total === 0
          ? "Sin resultados"
          : `${formatNumber(total)} ${total === 1 ? "entidad" : "entidades"}, en orden alfabético`}
      </p>
      {total === 0 ? (
        <Notice>
          {hasFilters
            ? "Ninguna entidad coincide con esta búsqueda. Puede probar con menos palabras o quitar filtros."
            : "Todavía no se han cargado datos de ejecución presupuestal."}
        </Notice>
      ) : (
        <ul className="rounded border border-rule bg-surface px-5">
          {items.map((item) => (
            <li key={item.entity_code} className="border-t border-rule py-4 first:border-t-0">
              <h3 className="text-lg font-semibold">
                <Link href={`${BASE_PATH}/${item.entity_code}`} className={linkClass}>
                  {item.entity_name}
                </Link>
              </h3>
              <p className="mt-1 text-ink-muted">
                {[
                  item.sector_name,
                  `Apropiación ${formatPesosShort(item.amounts.appropriation)}`,
                  `comprometido ${formatRate(item.rates.commitments)}`,
                  `pagado ${formatRate(item.rates.payments)}`,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            </li>
          ))}
        </ul>
      )}
      <Pagination basePath={BASE_PATH} query={filters} page={page} pageSize={PAGE_SIZE} total={total} />
    </section>
  );
}

export default function PresupuestoPage(props: PageProps<"/presupuesto">) {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3">
        <h1 className="font-serif text-3xl font-semibold text-brand">Presupuesto</h1>
        <p className="max-w-3xl text-ink-muted">
          Ejecución del Presupuesto General de la Nación por entidad del nivel nacional, según el
          conjunto de datos que publica el Ministerio de Hacienda y Crédito Público. Las cifras son
          las de la fuente; NEXO solo suma y calcula porcentajes, y lo indica.
        </p>
      </div>
      <Suspense fallback={<p role="status">Cargando el resumen…</p>}>
        <Summary />
      </Suspense>
      <Suspense fallback={<p role="status">Cargando las entidades…</p>}>
        <Directory searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

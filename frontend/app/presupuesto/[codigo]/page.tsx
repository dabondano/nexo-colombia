import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { AssociationNote } from "@/components/AssociationNote";
import { BudgetFigures, BudgetNotes } from "@/components/BudgetFigures";
import { Notice } from "@/components/Notice";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { ScrollRegion } from "@/components/ScrollRegion";
import { fetchBudgetEntity } from "@/lib/api";
import { formatCalendarDate, formatPesos, formatRate } from "@/lib/format";

const linkClass = "text-brand underline underline-offset-4";

export async function generateMetadata(props: PageProps<"/presupuesto/[codigo]">): Promise<Metadata> {
  const { codigo } = await props.params;
  const result = await fetchBudgetEntity(codigo);
  return { title: result.ok ? `Presupuesto: ${result.data.entity_name}` : "Presupuesto" };
}

async function EntityBudgetRecord({ params }: { params: Promise<{ codigo: string }> }) {
  const { codigo } = await params;
  const result = await fetchBudgetEntity(codigo);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <Notice>{result.reason} Este registro no está disponible en este momento.</Notice>;
  }
  const entity = result.data;
  return (
    <article className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          Ejecución presupuestal{entity.sector_name ? ` · ${entity.sector_name}` : ""}
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">{entity.entity_name}</h1>
        <p className="text-sm text-ink-muted">Código en el Presupuesto General de la Nación: {entity.entity_code}</p>
      </header>
      {entity.linked_institution ? (
        <section aria-labelledby="titulo-entidad" className="rounded border border-rule bg-surface p-5">
          <h2 id="titulo-entidad" className="text-xl font-semibold">
            En el directorio de entidades
          </h2>
          <p className="mt-3 text-sm">
            <Link
              href={`/instituciones/${entity.linked_institution.institution_id}`}
              className={linkClass}
            >
              {entity.linked_institution.name}
            </Link>
          </p>
          <AssociationNote
            label={entity.linked_institution_label}
            rule={entity.linked_institution_rule}
          />
        </section>
      ) : null}
      <BudgetFigures amounts={entity.amounts} rates={entity.rates} />
      <BudgetNotes yearNote={entity.year_note} formula={entity.rate_formula} />
      <section aria-labelledby="titulo-lineas" className="flex flex-col gap-3">
        <h2 id="titulo-lineas" className="text-xl font-semibold">
          Por fuente y recurso
        </h2>
        <ScrollRegion label={`Tabla de ejecución de ${entity.entity_name}`} className="rounded border border-rule bg-surface">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">
              Ejecución de {entity.entity_name} por fuente de financiación y recurso
            </caption>
            <thead>
              <tr className="border-b border-rule">
                <th scope="col" className="p-3">Fuente y recurso</th>
                <th scope="col" className="p-3 text-right">Apropiación</th>
                <th scope="col" className="p-3 text-right">Compromisos</th>
                <th scope="col" className="p-3 text-right">Obligaciones</th>
                <th scope="col" className="p-3 text-right">Pagos</th>
              </tr>
            </thead>
            <tbody>
              {entity.lines.map((line) => (
                <tr
                  key={`${line.funding_source}-${line.funds_situation}-${line.budget_resource}`}
                  className="border-t border-rule align-top"
                >
                  <th scope="row" className="p-3 font-normal">
                    {[line.funding_source, line.funds_situation, line.budget_resource]
                      .filter(Boolean)
                      .join(" · ")}
                    {line.data_quality_status === "conflicting" ? (
                      <span className="block text-warn">
                        Las etapas no son coherentes en la fuente (una etapa supera a la anterior).
                      </span>
                    ) : null}
                  </th>
                  <td className="p-3 text-right">{formatPesos(line.amounts.appropriation)}</td>
                  <td className="p-3 text-right">
                    {formatPesos(line.amounts.commitments)}
                    <span className="block text-ink-muted">{formatRate(line.rates.commitments)}</span>
                  </td>
                  <td className="p-3 text-right">
                    {formatPesos(line.amounts.obligations)}
                    <span className="block text-ink-muted">{formatRate(line.rates.obligations)}</span>
                  </td>
                  <td className="p-3 text-right">
                    {formatPesos(line.amounts.payments)}
                    <span className="block text-ink-muted">{formatRate(line.rates.payments)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollRegion>
      </section>
      <section aria-labelledby="titulo-historial" className="flex flex-col gap-3">
        <h2 id="titulo-historial" className="text-xl font-semibold">
          Cifras en cada actualización de la fuente
        </h2>
        <p className="text-sm text-ink-muted">{entity.history_note}</p>
        {entity.history.length < 2 ? (
          <p className="text-sm">
            {entity.history.length === 0
              ? "NEXO todavía no ha guardado cifras de esta entidad."
              : "Por ahora NEXO solo tiene las cifras de una actualización; la comparación aparecerá cuando la fuente publique la siguiente."}
          </p>
        ) : null}
        {entity.history.length > 0 ? (
          <ScrollRegion
            label={`Historial de cifras de ${entity.entity_name}`}
            className="rounded border border-rule bg-surface"
          >
            <table className="w-full text-left text-sm">
              <caption className="sr-only">
                Cifras de {entity.entity_name} en cada actualización publicada por la fuente
              </caption>
              <thead>
                <tr className="border-b border-rule">
                  <th scope="col" className="p-3">Actualización de la fuente</th>
                  <th scope="col" className="p-3 text-right">Apropiación</th>
                  <th scope="col" className="p-3 text-right">Compromisos</th>
                  <th scope="col" className="p-3 text-right">Obligaciones</th>
                  <th scope="col" className="p-3 text-right">Pagos</th>
                </tr>
              </thead>
              <tbody>
                {entity.history.map((row) => (
                  <tr key={row.published_on} className="border-t border-rule align-top">
                    <th scope="row" className="p-3 font-normal">
                      {formatCalendarDate(row.published_on)}
                    </th>
                    <td className="p-3 text-right">{formatPesos(row.amounts.appropriation)}</td>
                    <td className="p-3 text-right">
                      {formatPesos(row.amounts.commitments)}
                      <span className="block text-ink-muted">{formatRate(row.rates.commitments)}</span>
                    </td>
                    <td className="p-3 text-right">
                      {formatPesos(row.amounts.obligations)}
                      <span className="block text-ink-muted">{formatRate(row.rates.obligations)}</span>
                    </td>
                    <td className="p-3 text-right">
                      {formatPesos(row.amounts.payments)}
                      <span className="block text-ink-muted">{formatRate(row.rates.payments)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollRegion>
        ) : null}
      </section>
      <ProvenancePanel
        provenance={entity.provenance}
        epistemicLabel={entity.epistemic_label}
        dataQualityStatus={entity.data_quality_status}
      />
    </article>
  );
}

export default function PresupuestoEntidadPage(props: PageProps<"/presupuesto/[codigo]">) {
  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación">
        <Link href="/presupuesto" className={linkClass}>
          Volver al presupuesto
        </Link>
      </nav>
      <Suspense fallback={<p role="status">Cargando el registro…</p>}>
        <EntityBudgetRecord params={props.params} />
      </Suspense>
    </div>
  );
}

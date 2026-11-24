import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { AssociationNote } from "@/components/AssociationNote";
import { Field, NOT_IN_SOURCE, Notice } from "@/components/Notice";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { fetchContract } from "@/lib/api";
import { formatCalendarDate, formatDateTime, formatPesos } from "@/lib/format";

const linkClass = "text-brand underline underline-offset-4";

export async function generateMetadata(props: PageProps<"/contratos/[id]">): Promise<Metadata> {
  const { id } = await props.params;
  const result = await fetchContract(id);
  return { title: result.ok ? `Contrato ${result.data.source_key}` : "Contrato" };
}

function value(text: string | null | undefined): string {
  return text ?? NOT_IN_SOURCE;
}

function money(amount: string | null): string {
  return amount === null ? NOT_IN_SOURCE : formatPesos(amount);
}

async function ContractRecord({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await fetchContract(id);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <Notice>{result.reason} Este registro no está disponible en este momento.</Notice>;
  }
  const contract = result.data;
  const place = [contract.city, contract.department].filter(Boolean).join(", ");
  return (
    <article className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          Contrato · {contract.source_key}
        </p>
        <h1 className="font-serif text-2xl font-semibold text-brand">{contract.purpose}</h1>
        <p className="text-ink-muted">
          {contract.entity_name} · firmado el {formatCalendarDate(contract.signed_on)}
        </p>
      </header>

      <section aria-labelledby="titulo-valores" className="rounded border border-rule bg-surface p-5">
        <h2 id="titulo-valores" className="text-xl font-semibold">
          Valores
        </h2>
        <dl className="mt-3 text-sm">
          <Field term="Valor del contrato">{formatPesos(contract.value)}</Field>
          <Field term="Facturado">{money(contract.invoiced)}</Field>
          <Field term="Pagado">{money(contract.paid)}</Field>
          <Field term="Pendiente de pago">{money(contract.pending_payment)}</Field>
          <Field term="Pendiente de ejecución">{money(contract.pending_execution)}</Field>
        </dl>
        <p className="mt-3 text-sm text-ink-muted">{contract.value_note}</p>
        {contract.data_quality_status === "conflicting" ? (
          <p className="mt-2 text-sm text-warn">
            Las cifras no son coherentes en la fuente: lo facturado supera el valor del contrato o
            lo pagado supera lo facturado.
          </p>
        ) : null}
      </section>

      <section aria-labelledby="titulo-datos" className="rounded border border-rule bg-surface p-5">
        <h2 id="titulo-datos" className="text-xl font-semibold">
          Datos del contrato
        </h2>
        <dl className="mt-3 text-sm">
          <Field term="Entidad contratante">{contract.entity_name}</Field>
          <Field term="NIT de la entidad">{value(contract.entity_nit)}</Field>
          <Field term="Contratista">
            {contract.supplier_name ?? contract.supplier_label}
            {contract.supplier_nit ? (
              <span className="text-ink-muted"> (NIT {contract.supplier_nit})</span>
            ) : null}
          </Field>
          <Field term="Tipo de contratista">{contract.supplier_label}</Field>
          <Field term="Tipo de contrato">{value(contract.contract_type)}</Field>
          <Field term="Modalidad de contratación">{value(contract.modality)}</Field>
          <Field term="Justificación de la modalidad">{value(contract.modality_reason)}</Field>
          <Field term="Estado">{value(contract.status)}</Field>
          <Field term="Inicio y fin">
            {contract.start_on ? formatCalendarDate(contract.start_on) : NOT_IN_SOURCE} –{" "}
            {contract.end_on ? formatCalendarDate(contract.end_on) : NOT_IN_SOURCE}
          </Field>
          <Field term="Duración">{value(contract.duration_text)}</Field>
          <Field term="Días adicionados">
            {contract.days_added === null ? NOT_IN_SOURCE : String(contract.days_added)}
          </Field>
          <Field term="Origen de los recursos">{value(contract.resource_origin)}</Field>
          <Field term="Destino del gasto">{value(contract.spending_type)}</Field>
          <Field term="Sector">{value(contract.sector)}</Field>
          <Field term="Lugar">{place || NOT_IN_SOURCE}</Field>
          <Field term="Referencia">{value(contract.reference)}</Field>
          <Field term="Proceso en SECOP">
            {contract.process_url ? (
              <a href={contract.process_url} className={`break-all ${linkClass}`} rel="noopener noreferrer">
                {contract.process_id ?? "Ver el proceso"}
              </a>
            ) : (
              value(contract.process_id)
            )}
          </Field>
          <Field term="Última actualización en SECOP">
            {contract.source_updated_at ? formatDateTime(contract.source_updated_at) : NOT_IN_SOURCE}
          </Field>
        </dl>
        <p className="mt-3 text-sm text-ink-muted">{contract.privacy_note}</p>
      </section>

      {contract.institution ? (
        <section aria-labelledby="titulo-entidad" className="rounded border border-rule bg-surface p-5">
          <h2 id="titulo-entidad" className="text-xl font-semibold">
            En el directorio de entidades
          </h2>
          <p className="mt-3 text-sm">
            <Link href={`/instituciones/${contract.institution.institution_id}`} className={linkClass}>
              {contract.institution.name}
            </Link>
          </p>
          <AssociationNote label={contract.epistemic_label} rule={contract.institution_rule} />
        </section>
      ) : null}

      <p className="text-sm text-ink-muted">{contract.window_note}</p>
      <ProvenancePanel
        provenance={contract.provenance}
        epistemicLabel={contract.epistemic_label}
        dataQualityStatus={contract.data_quality_status}
      />
    </article>
  );
}

export default function ContratoPage(props: PageProps<"/contratos/[id]">) {
  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación">
        <Link href="/contratos" className={linkClass}>
          Volver a los contratos
        </Link>
      </nav>
      <Suspense fallback={<p role="status">Cargando el registro…</p>}>
        <ContractRecord params={props.params} />
      </Suspense>
    </div>
  );
}

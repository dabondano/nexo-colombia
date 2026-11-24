import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Field, NOT_IN_SOURCE, Notice } from "@/components/Notice";
import { AssociationNote } from "@/components/AssociationNote";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { fetchInitiative } from "@/lib/api";
import { formatCalendarDate } from "@/lib/format";

export async function generateMetadata(props: PageProps<"/legislacion/[id]">): Promise<Metadata> {
  const { id } = await props.params;
  const result = await fetchInitiative(id);
  if (!result.ok) return { title: "Iniciativa legislativa" };
  return { title: result.data.short_title ?? result.data.title.slice(0, 80) };
}

async function InitiativeRecord({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await fetchInitiative(id);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <Notice>{result.reason} Este registro no está disponible en este momento.</Notice>;
  }
  const bill = result.data;
  const value = (text: string | null) => text ?? NOT_IN_SOURCE;
  const date = (text: string | null) => (text ? formatCalendarDate(text) : NOT_IN_SOURCE);

  return (
    <article className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          Iniciativa legislativa{bill.law_type ? ` · ${bill.law_type}` : ""}
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">
          {bill.short_title ?? bill.title}
        </h1>
        {bill.short_title ? <p className="max-w-3xl text-lg">{bill.title}</p> : null}
      </header>

      <section aria-labelledby="titulo-datos" className="rounded border border-rule bg-surface p-5">
        <h2 id="titulo-datos" className="text-xl font-semibold">
          Datos del proyecto
        </h2>
        <dl className="mt-3 text-sm">
          <Field term="Estado según la fuente">{value(bill.status)}</Field>
          <Field term="Número en Cámara">{value(bill.camara_number)}</Field>
          <Field term="Radicado en Cámara">{date(bill.camara_filed_on)}</Field>
          <Field term="Número en Senado">{value(bill.senado_number)}</Field>
          <Field term="Radicado en Senado">{date(bill.senado_filed_on)}</Field>
          <Field term="Legislatura">{value(bill.legislature)}</Field>
          <Field term="Cámara de origen">{value(bill.origin_chamber)}</Field>
          <Field term="Comisión">{value(bill.commission)}</Field>
          <Field term="Autores (texto de la fuente)">{value(bill.authors_text)}</Field>
          <Field term="Objeto">{value(bill.purpose)}</Field>
          {bill.observations ? <Field term="Observaciones">{bill.observations}</Field> : null}
        </dl>
        <p className="mt-4 text-sm text-ink-muted">
          Los autores aparecen como texto, tal como los publica la fuente. La fuente no incluye
          el historial de debates ni las votaciones.
        </p>
      </section>

      {bill.linked_authors.length > 0 ? (
        <section
          aria-labelledby="titulo-autores"
          className="rounded border border-rule bg-surface p-5"
        >
          <h2 id="titulo-autores" className="text-xl font-semibold">
            Autores con ficha de representante
          </h2>
          <ul className="mt-3 flex list-disc flex-col gap-1 pl-5 text-sm">
            {bill.linked_authors.map((author) => (
              <li key={author.representative_id}>
                <Link
                  href={`/representantes/${author.representative_id}`}
                  className="text-brand underline underline-offset-4"
                >
                  {author.full_name}
                </Link>
                {author.author_name !== author.full_name ? (
                  <span className="text-ink-muted"> (en la fuente: «{author.author_name}»)</span>
                ) : null}
              </li>
            ))}
          </ul>
          <AssociationNote label={bill.linked_authors_label} rule={bill.linked_authors_rule} />
        </section>
      ) : null}

      <ProvenancePanel
        provenance={bill.provenance}
        epistemicLabel={bill.epistemic_label}
        dataQualityStatus={bill.data_quality_status}
      />
    </article>
  );
}

export default function IniciativaPage(props: PageProps<"/legislacion/[id]">) {
  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación">
        <Link href="/legislacion" className="text-brand underline underline-offset-4">
          Volver a los proyectos de ley
        </Link>
      </nav>
      <Suspense fallback={<p role="status">Cargando el registro…</p>}>
        <InitiativeRecord params={props.params} />
      </Suspense>
    </div>
  );
}

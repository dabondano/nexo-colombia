import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Notice } from "@/components/Notice";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { ProvisionReviewNotice } from "@/components/ReviewNotice";
import { SourceText, hasStruckText } from "@/components/SourceText";
import {
  fetchConstitutionProvision,
  type Provision,
  type ProvisionRef,
  type Segment,
} from "@/lib/api";

const linkClass = "text-brand underline underline-offset-4";
const CONSTITUTION = "Constitución Política de 1991";

export async function generateMetadata(
  props: PageProps<"/constitucion/[clave]">,
): Promise<Metadata> {
  const { clave } = await props.params;
  const result = await fetchConstitutionProvision(clave);
  return {
    title: result.ok ? `${result.data.label} · ${CONSTITUTION}` : CONSTITUTION,
  };
}

function refLabel(ref: ProvisionRef): string {
  return ref.heading ? `${ref.label}. ${ref.heading}` : ref.label;
}

function SegmentBlock({ segment }: { segment: Segment }) {
  if (segment.kind === "note") {
    return (
      <p className="border-l-4 border-rule pl-3 text-sm text-ink-muted">
        <span className="font-medium">Nota de la fuente: </span>
        {segment.text}
      </p>
    );
  }
  if (segment.kind === "after_previous_mark") {
    return (
      <p className="border-l-4 border-warn pl-3 text-ink-muted">
        <span className="block text-sm font-medium text-warn">
          Impreso después de la marca «TEXTO ANTERIOR»: puede no estar vigente
        </span>
        <SourceText text={segment.text} />
      </p>
    );
  }
  return (
    <p className="text-lg leading-relaxed">
      <SourceText text={segment.text} />
    </p>
  );
}

function ReviewWarning({ provision }: { provision: Provision }) {
  const afterMark = provision.segments.some(
    (s) => s.kind === "after_previous_mark",
  );
  const struck = provision.segments.some((s) => hasStruckText(s.text));
  const noWording = !provision.segments.some((s) => s.kind === "text");
  if (!afterMark && !struck && !noWording) return null;
  return (
    <section
      aria-labelledby="titulo-revision"
      className="rounded border border-warn bg-surface p-5"
    >
      <h2 id="titulo-revision" className="text-lg font-semibold text-warn">
        Este artículo requiere revisión con la fuente oficial
      </h2>
      <ul className="mt-2 list-disc pl-5">
        {afterMark ? (
          <li>
            La fuente imprime texto después de su marca «TEXTO ANTERIOR» y no
            indica dónde termina el texto anterior. Lo que aparece después de
            esa marca puede incluir texto que ya no está vigente y también
            incisos vigentes.
          </li>
        ) : null}
        {struck ? (
          <li>
            La fuente muestra palabras tachadas. Aquí aparecen tachadas y no se
            buscan.
          </li>
        ) : null}
        {noWording ? (
          <li>La fuente no imprime texto vigente para este artículo.</li>
        ) : null}
      </ul>
    </section>
  );
}

function Neighbour({
  item,
  label,
}: {
  item: ProvisionRef | null;
  label: string;
}) {
  if (!item) return <span />;
  return (
    <Link href={`/constitucion/${item.path}`} className={linkClass}>
      {label}: {item.label}
    </Link>
  );
}

async function ProvisionRecord({
  params,
}: {
  params: Promise<{ clave: string }>;
}) {
  const { clave } = await params;
  const result = await fetchConstitutionProvision(clave);
  if (!result.ok) {
    if (result.notFound) notFound();
    return (
      <Notice>
        {result.reason} Este artículo no está disponible en este momento.
      </Notice>
    );
  }
  const provision = result.data;

  return (
    <article className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          {CONSTITUTION}
          {provision.ancestors.map((ancestor) => (
            <span
              key={ancestor.id}
              className="normal-case tracking-normal text-ink-muted"
            >
              {" "}
              · {refLabel(ancestor)}
            </span>
          ))}
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">
          {refLabel(provision)}
        </h1>
      </header>

      <ReviewWarning provision={provision} />

      <section
        aria-label="Texto según la fuente"
        className="flex max-w-3xl flex-col gap-4"
      >
        {provision.segments.length === 0 ? (
          <Notice>La fuente no imprime texto para esta parte.</Notice>
        ) : (
          provision.segments.map((segment, index) => (
            <SegmentBlock key={index} segment={segment} />
          ))
        )}
      </section>

      <nav
        aria-label="Artículos vecinos"
        className="flex flex-wrap justify-between gap-4"
      >
        <Neighbour item={provision.previous} label="Anterior" />
        <Neighbour item={provision.next} label="Siguiente" />
      </nav>

      <Suspense fallback={null}>
        <ProvisionReviewNotice path={provision.path} versionId={provision.version_id} />
      </Suspense>

      <p className="max-w-3xl text-sm text-ink-muted">
        {provision.instrument.edition_note}
      </p>

      <ProvenancePanel
        provenance={provision.provenance}
        epistemicLabel="hecho_documentado"
        dataQualityStatus={provision.data_quality_status}
        qualityMeaning={
          provision.data_quality_status === "incomplete"
            ? "La fuente mezcla el texto de este artículo con texto anterior o tachado, o no imprime texto."
            : "El texto se muestra tal como lo publica la fuente, que es una edición informativa."
        }
      />
    </article>
  );
}

export default function ProvisionPage(
  props: PageProps<"/constitucion/[clave]">,
) {
  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación">
        <Link href="/constitucion" className={linkClass}>
          Volver al índice de la Constitución
        </Link>
      </nav>
      <Suspense fallback={<p role="status">Cargando el artículo…</p>}>
        <ProvisionRecord params={props.params} />
      </Suspense>
    </div>
  );
}

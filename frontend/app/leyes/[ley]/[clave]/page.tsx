import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Notice } from "@/components/Notice";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { ProvisionText, ReviewWarning } from "@/components/ProvisionText";
import { fetchLawProvision, lawName, type ProvisionRef } from "@/lib/api";

const linkClass = "text-brand underline underline-offset-4";

export async function generateMetadata(
  props: PageProps<"/leyes/[ley]/[clave]">,
): Promise<Metadata> {
  const { ley, clave } = await props.params;
  const result = await fetchLawProvision(ley, clave);
  return {
    title: result.ok ? `${result.data.label} · ${lawName(result.data.instrument)}` : "Ley",
  };
}

function refLabel(ref: ProvisionRef): string {
  return ref.heading ? `${ref.label}. ${ref.heading}` : ref.label;
}

function Neighbour({ item, label, slug }: { item: ProvisionRef | null; label: string; slug: string }) {
  if (!item) return <span />;
  return (
    <Link href={`/leyes/${slug}/${item.path}`} className={linkClass}>
      {label}: {item.label}
    </Link>
  );
}

async function ProvisionRecord({ params }: { params: Promise<{ ley: string; clave: string }> }) {
  const { ley, clave } = await params;
  const result = await fetchLawProvision(ley, clave);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <Notice>{result.reason} Este artículo no está disponible en este momento.</Notice>;
  }
  const provision = result.data;
  const name = lawName(provision.instrument);
  return (
    <article className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          {name}
          {provision.ancestors.map((ancestor) => (
            <span key={ancestor.id} className="normal-case tracking-normal text-ink-muted">
              {" "}
              · {refLabel(ancestor)}
            </span>
          ))}
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">{refLabel(provision)}</h1>
      </header>

      <ReviewWarning provision={provision} />

      <section aria-label="Texto según la fuente" className="flex max-w-3xl flex-col gap-4">
        <ProvisionText segments={provision.segments} />
      </section>

      <nav aria-label="Artículos vecinos" className="flex flex-wrap justify-between gap-4">
        <Neighbour item={provision.previous} label="Anterior" slug={ley} />
        <Neighbour item={provision.next} label="Siguiente" slug={ley} />
      </nav>

      <p className="max-w-3xl text-sm text-ink-muted">{provision.instrument.edition_note}</p>

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

export default function LeyArticuloPage(props: PageProps<"/leyes/[ley]/[clave]">) {
  return (
    <div className="flex flex-col gap-6">
      <Suspense fallback={<p role="status">Cargando el artículo…</p>}>
        <BackLink params={props.params} />
        <ProvisionRecord params={props.params} />
      </Suspense>
    </div>
  );
}

async function BackLink({ params }: { params: Promise<{ ley: string }> }) {
  const { ley } = await params;
  return (
    <nav aria-label="Ruta de navegación">
      <Link href={`/leyes/${ley}`} className={linkClass}>
        Volver al índice de la ley
      </Link>
    </nav>
  );
}

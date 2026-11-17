import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Field, NOT_IN_SOURCE, Notice } from "@/components/Notice";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { fetchInstitution } from "@/lib/api";

export async function generateMetadata(
  props: PageProps<"/instituciones/[id]">,
): Promise<Metadata> {
  const { id } = await props.params;
  const result = await fetchInstitution(id);
  return { title: result.ok ? result.data.name : "Entidad" };
}

async function InstitutionRecord({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await fetchInstitution(id);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <Notice>{result.reason} Este registro no está disponible en este momento.</Notice>;
  }
  const entity = result.data;
  const value = (text: string | null) => text ?? NOT_IN_SOURCE;
  const place = [entity.municipality, entity.department].filter(Boolean).join(", ");

  return (
    <article className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">Entidad pública</p>
        <h1 className="font-serif text-3xl font-semibold text-brand">{entity.name}</h1>
      </header>

      <section aria-labelledby="titulo-datos" className="rounded border border-rule bg-surface p-5">
        <h2 id="titulo-datos" className="text-xl font-semibold">
          Datos del directorio
        </h2>
        <dl className="mt-3 text-sm">
          <Field term="Orden">{value(entity.order)}</Field>
          <Field term="Suborden">{value(entity.suborder)}</Field>
          <Field term="Clasificación orgánica">{value(entity.organic_classification)}</Field>
          <Field term="Sector administrativo">{value(entity.sector)}</Field>
          <Field term="Naturaleza jurídica">{value(entity.legal_nature)}</Field>
          <Field term="Nivel">{value(entity.level)}</Field>
          <Field term="Tipo de vinculación">{value(entity.institution_type)}</Field>
          <Field term="Ubicación">{place || NOT_IN_SOURCE}</Field>
          <Field term="NIT">{value(entity.nit)}</Field>
          <Field term="Código en Función Pública">{entity.official_code}</Field>
          <Field term="Estado en el directorio">{value(entity.status)}</Field>
          <Field term="Sitio web">
            {entity.website ? (
              <a
                href={entity.website}
                className="break-all text-brand underline underline-offset-4"
                rel="noopener noreferrer"
              >
                {entity.website}
              </a>
            ) : (
              NOT_IN_SOURCE
            )}
          </Field>
        </dl>
      </section>

      <ProvenancePanel
        provenance={entity.provenance}
        epistemicLabel={entity.epistemic_label}
        dataQualityStatus={entity.data_quality_status}
      />
    </article>
  );
}

export default function InstitucionPage(props: PageProps<"/instituciones/[id]">) {
  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación">
        <Link href="/instituciones" className="text-brand underline underline-offset-4">
          Volver al directorio de instituciones
        </Link>
      </nav>
      <Suspense fallback={<p role="status">Cargando el registro…</p>}>
        <InstitutionRecord params={props.params} />
      </Suspense>
    </div>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { AssociationNote } from "@/components/AssociationNote";
import { Field, NOT_IN_SOURCE, Notice } from "@/components/Notice";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { fetchRepresentative } from "@/lib/api";

const linkClass = "text-brand underline underline-offset-4";

export async function generateMetadata(
  props: PageProps<"/representantes/[id]">,
): Promise<Metadata> {
  const { id } = await props.params;
  const result = await fetchRepresentative(id);
  return { title: result.ok ? result.data.full_name : "Representante" };
}

async function RepresentativeRecord({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await fetchRepresentative(id);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <Notice>{result.reason} Este registro no está disponible en este momento.</Notice>;
  }
  const member = result.data;
  const value = (text: string | null) => text ?? NOT_IN_SOURCE;
  const bills = member.authored_initiatives;

  return (
    <article className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          {member.position} · Período {member.period}
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">{member.full_name}</h1>
      </header>

      <section aria-labelledby="titulo-datos" className="rounded border border-rule bg-surface p-5">
        <h2 id="titulo-datos" className="text-xl font-semibold">
          Datos de la Cámara
        </h2>
        <dl className="mt-3 text-sm">
          <Field term="Corporación">{member.corporation}</Field>
          <Field term="Circunscripción">{value(member.constituency)}</Field>
          {member.seat_basis ? (
            <Field term="Fundamento de la curul">{member.seat_basis}</Field>
          ) : (
            <Field term="Partido, movimiento u organización">{value(member.party)}</Field>
          )}
        </dl>
      </section>

      <section
        aria-labelledby="titulo-contacto"
        className="rounded border border-rule bg-surface p-5"
      >
        <h2 id="titulo-contacto" className="text-xl font-semibold">
          Contacto institucional
        </h2>
        <dl className="mt-3 text-sm">
          <Field term="Correo">
            {member.email ? (
              <a href={`mailto:${member.email}`} className={`break-all ${linkClass}`}>
                {member.email}
              </a>
            ) : (
              NOT_IN_SOURCE
            )}
          </Field>
          <Field term="Oficina">{value(member.office)}</Field>
          <Field term="Teléfono">{value(member.phone)}</Field>
        </dl>
        <p className="mt-4 text-sm text-ink-muted">
          Datos de contacto del cargo, publicados por la Cámara de Representantes.
        </p>
      </section>

      <section
        aria-labelledby="titulo-proyectos"
        className="rounded border border-rule bg-surface p-5"
      >
        <h2 id="titulo-proyectos" className="text-xl font-semibold">
          Proyectos de ley en los que figura como autor
        </h2>
        {bills.length === 0 ? (
          <p className="mt-3 text-sm text-ink-muted">
            NEXO no encontró proyectos radicados desde el 20 de julio de 2026 en los que este
            nombre figure exactamente entre los autores.
          </p>
        ) : (
          <>
            <p className="mt-3 text-sm text-ink-muted">
              {bills.length === 1 ? "1 proyecto" : `${bills.length} proyectos`}, del más reciente
              al más antiguo.
            </p>
            <ul className="mt-3 flex flex-col gap-3 text-sm">
              {bills.map((bill) => (
                <li key={bill.id}>
                  <Link href={`/legislacion/${bill.id}`} className={linkClass}>
                    {bill.title}
                  </Link>
                  <span className="block text-ink-muted">
                    {[
                      bill.camara_number ? `Cámara ${bill.camara_number}` : null,
                      bill.senado_number ? `Senado ${bill.senado_number}` : null,
                      bill.status,
                    ]
                      .filter(Boolean)
                      .join(" · ")}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
        <AssociationNote
          label={member.authored_initiatives_label}
          rule={member.authored_initiatives_rule}
        />
      </section>

      <ProvenancePanel
        provenance={member.provenance}
        epistemicLabel={member.epistemic_label}
        dataQualityStatus={member.data_quality_status}
      />
    </article>
  );
}

export default function RepresentantePage(props: PageProps<"/representantes/[id]">) {
  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Ruta de navegación">
        <Link href="/representantes" className={linkClass}>
          Volver al directorio de representantes
        </Link>
      </nav>
      <Suspense fallback={<p role="status">Cargando el registro…</p>}>
        <RepresentativeRecord params={props.params} />
      </Suspense>
    </div>
  );
}

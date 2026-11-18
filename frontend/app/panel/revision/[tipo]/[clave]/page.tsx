import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { Notice } from "@/components/Notice";
import { ReviewForm } from "@/components/StaffForms";
import { fetchConstitutionProvision } from "@/lib/api";
import { LESSONS } from "@/lib/lessons";
import { lessonFingerprint } from "@/lib/review";
import { DECISION_LABELS } from "@/lib/staff-labels";
import { formatTimestamp, requireStaff, staffRequest } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Revisar contenido",
  robots: { index: false, follow: false },
};

const linkClass = "text-brand underline underline-offset-4";

type Review = {
  id: string;
  fingerprint: string;
  decision: string;
  notes: string;
  reviewer_name: string | null;
  reviewer_email: string | null;
  reviewed_at: string;
};

const TYPES = { leccion: "lesson", articulo: "constitution_provision" } as const;

async function Item({ params }: { params: Promise<{ tipo: string; clave: string }> }) {
  const { user, allowed } = await requireStaff(["legal_reviewer"]);
  const { tipo, clave } = await params;
  const contentType = TYPES[tipo as keyof typeof TYPES];

  let title: string | null = null;
  let publicPath = "";
  let fingerprint: string | null = null;
  if (contentType === "lesson") {
    const lesson = LESSONS.find((item) => item.slug === clave);
    if (lesson) {
      title = `Lección: ${lesson.title}`;
      publicPath = `/aprender/${lesson.slug}`;
      fingerprint = lessonFingerprint(lesson);
    }
  } else if (contentType === "constitution_provision") {
    const provision = await fetchConstitutionProvision(clave);
    if (provision.ok) {
      title = `Constitución: ${provision.data.label}`;
      publicPath = `/constitucion/${provision.data.path}`;
      fingerprint = provision.data.version_id;
    }
  }

  if (!allowed || title === null || !contentType) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Revisar contenido" />
        {!allowed ? <Forbidden /> : <Notice>Este contenido no existe.</Notice>}
      </div>
    );
  }

  const history = await staffRequest<Review[]>("/reviews", {
    params: { content_type: contentType, content_key: clave },
  });

  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title={title} />
      <p className="text-sm">
        <Link href="/panel/revision" className={linkClass}>
          Volver a la revisión jurídica
        </Link>{" "}
        ·{" "}
        <Link href={publicPath} className={linkClass}>
          Abrir el contenido tal como se publica
        </Link>
      </p>
      <section aria-labelledby="titulo-registrar" className="flex flex-col gap-3">
        <h2 id="titulo-registrar" className="text-xl font-semibold">
          Registrar una revisión
        </h2>
        <p className="max-w-3xl text-sm text-ink-muted">
          La decisión se aplica al contenido publicado en este momento. Si después cambia, la
          aprobación deja de mostrarse y el contenido vuelve a quedar pendiente.
        </p>
        <ReviewForm contentType={contentType} contentKey={clave} />
      </section>
      <section aria-labelledby="titulo-historial" className="flex flex-col gap-3">
        <h2 id="titulo-historial" className="text-xl font-semibold">
          Historial
        </h2>
        {!history.ok ? (
          <Notice>{history.reason}</Notice>
        ) : history.data.length === 0 ? (
          <Notice>Todavía no hay revisiones de este contenido.</Notice>
        ) : (
          <ul className="flex flex-col gap-3">
            {history.data.map((review) => (
              <li key={review.id} className="rounded border border-rule bg-surface p-4 text-sm">
                <p>
                  <span className="font-medium">{DECISION_LABELS[review.decision]}</span> ·{" "}
                  {formatTimestamp(review.reviewed_at)} · {review.reviewer_name} (
                  {review.reviewer_email})
                  {review.fingerprint === fingerprint ? (
                    " · Corresponde al contenido actual"
                  ) : (
                    <span className="text-warn"> · El contenido cambió después de esta revisión</span>
                  )}
                </p>
                {review.notes ? <p className="mt-2 whitespace-pre-wrap">{review.notes}</p> : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

export default function RevisarPage(props: PageProps<"/panel/revision/[tipo]/[clave]">) {
  return (
    <Suspense fallback={<p role="status">Cargando…</p>}>
      <Item params={props.params} />
    </Suspense>
  );
}

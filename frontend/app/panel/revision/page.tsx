import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import {
  CONSTITUTION_SLUG,
  fetchInstrument,
  fetchLatestReviews,
  type PublicReview,
} from "@/lib/api";
import { formatDateTime, formatNumber, pageNumber, type SearchParams } from "@/lib/format";
import { LESSONS } from "@/lib/lessons";
import { lessonFingerprint, reviewState, type ReviewState } from "@/lib/review";
import { DECISION_LABELS } from "@/lib/staff-labels";
import { requireStaff } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Revisión jurídica",
  robots: { index: false, follow: false },
};

const PAGE_SIZE = 25;
const linkClass = "text-brand underline underline-offset-4";

function status(review: PublicReview | undefined, state: ReviewState): string {
  if (state.kind === "reviewed") return `Aprobado el ${formatDateTime(state.date)}`;
  if (state.kind === "changed_since_review") {
    return `Cambió después de la aprobación del ${formatDateTime(state.date)}: revisar de nuevo`;
  }
  if (review) return `${DECISION_LABELS[review.decision]} el ${formatDateTime(review.reviewed_at)}`;
  return "Sin revisar";
}

async function Queue({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const { user, allowed } = await requireStaff(["legal_reviewer"]);
  if (!allowed) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Revisión jurídica" />
        <Forbidden />
      </div>
    );
  }
  const page = pageNumber(await searchParams);
  const [lessonReviews, articleReviews, constitution] = await Promise.all([
    fetchLatestReviews("lesson"),
    fetchLatestReviews("constitution_provision"),
    fetchInstrument(CONSTITUTION_SLUG),
  ]);
  const flagged = constitution.ok
    ? constitution.data.outline.filter(
        (item) => item.kind === "articulo" && item.data_quality_status === "incomplete",
      )
    : [];
  const shown = flagged.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const articleReview = (path: string) =>
    articleReviews.ok ? articleReviews.data.find((review) => review.content_key === path) : undefined;

  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Revisión jurídica" />
      <p className="max-w-3xl text-sm text-ink-muted">
        Una aprobación vale solo para el contenido exacto que se revisó: si una lección se edita o
        la fuente publica otra redacción de un artículo, vuelve a quedar pendiente. Las páginas
        públicas muestran la fecha de la aprobación, nunca las notas ni el nombre de quien revisa.
      </p>

      <section aria-labelledby="titulo-lecciones" className="flex flex-col gap-3">
        <h2 id="titulo-lecciones" className="text-xl font-semibold">
          Lecciones
        </h2>
        <ul className="rounded border border-rule bg-surface px-5">
          {LESSONS.map((lesson) => {
            const review = lessonReviews.ok
              ? lessonReviews.data.find((item) => item.content_key === lesson.slug)
              : undefined;
            const state = reviewState(review, lessonFingerprint(lesson));
            return (
              <li key={lesson.slug} className="border-t border-rule py-4 first:border-t-0">
                <Link href={`/panel/revision/leccion/${lesson.slug}`} className={linkClass}>
                  {lesson.title}
                </Link>
                <p className="mt-1 text-sm text-ink-muted">{status(review, state)}</p>
              </li>
            );
          })}
        </ul>
      </section>

      <section aria-labelledby="titulo-articulos" className="flex flex-col gap-3">
        <h2 id="titulo-articulos" className="text-xl font-semibold">
          Artículos marcados «Requiere revisión»
        </h2>
        {!constitution.ok ? (
          <Notice>{constitution.reason}</Notice>
        ) : flagged.length === 0 ? (
          <Notice>No hay artículos marcados para revisión.</Notice>
        ) : (
          <>
            <p role="status" className="text-sm">
              {formatNumber(flagged.length)} artículos en los que la fuente mezcla texto anterior o
              tachado (supuesto A-010). La ficha de cada artículo indica si su redacción
              cambió después de la última aprobación.
            </p>
            <ul className="rounded border border-rule bg-surface px-5">
              {shown.map((article) => (
                <li key={article.path} className="border-t border-rule py-3 first:border-t-0">
                  <Link href={`/panel/revision/articulo/${article.path}`} className={linkClass}>
                    {article.label}
                  </Link>
                  <span className="text-sm text-ink-muted">
                    {" "}
                    · {status(articleReview(article.path), { kind: "pending" })}
                  </span>
                </li>
              ))}
            </ul>
            <Pagination
              basePath="/panel/revision"
              query={{}}
              page={page}
              pageSize={PAGE_SIZE}
              total={flagged.length}
            />
          </>
        )}
      </section>
    </div>
  );
}

export default function RevisionPage(props: PageProps<"/panel/revision">) {
  return (
    <Suspense fallback={<p role="status">Cargando la revisión jurídica…</p>}>
      <Queue searchParams={props.searchParams} />
    </Suspense>
  );
}

import { fetchLatestReviews } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { LESSONS, REVIEW_STATUS } from "@/lib/lessons";
import { lessonFingerprint, reviewState, type ReviewState } from "@/lib/review";

const DISCLAIMER = "No es asesoría legal.";

function lessonText(state: ReviewState): string {
  switch (state.kind) {
    case "reviewed":
      return `Revisado por el equipo de revisión jurídica de NEXO el ${formatDateTime(state.date)}. ${DISCLAIMER}`;
    case "changed_since_review":
      return `El contenido cambió después de su última revisión jurídica (${formatDateTime(state.date)}); la versión actual está pendiente de revisión. ${DISCLAIMER}`;
    case "pending":
      return REVIEW_STATUS;
  }
}

/** The content status of one lesson, or of the whole path when no slug is given. */
export async function LessonReviewNotice({ slug, extra }: { slug?: string; extra?: string }) {
  const result = await fetchLatestReviews("lesson");
  const reviews = result.ok ? result.data : [];
  const lessons = slug ? LESSONS.filter((lesson) => lesson.slug === slug) : LESSONS;
  const states = lessons.map((lesson) =>
    reviewState(
      reviews.find((review) => review.content_key === lesson.slug),
      lessonFingerprint(lesson),
    ),
  );
  let text: string;
  if (slug) {
    text = lessonText(states[0] ?? { kind: "pending" });
  } else {
    const reviewed = states.filter((state) => state.kind === "reviewed").length;
    text =
      reviewed === lessons.length
        ? `Todas las lecciones fueron revisadas por el equipo de revisión jurídica de NEXO. ${DISCLAIMER}`
        : reviewed === 0
          ? REVIEW_STATUS
          : `${reviewed} de ${lessons.length} lecciones revisadas por el equipo de revisión jurídica de NEXO; cada lección indica su estado. ${DISCLAIMER}`;
  }
  const ok = slug ? states[0]?.kind === "reviewed" : states.every((s) => s.kind === "reviewed");
  return (
    <p role="note" className={`rounded border bg-surface p-4 text-sm ${ok ? "border-ok" : "border-warn"}`}>
      <span className={`font-semibold ${ok ? "text-ok" : "text-warn"}`}>Estado del contenido: </span>
      {text}
      {extra ? ` ${extra}` : null}
    </p>
  );
}

/** The draft notice, shown while the review status loads. */
export function LessonReviewFallback({ extra }: { extra?: string }) {
  return (
    <p role="note" className="rounded border border-warn bg-surface p-4 text-sm">
      <span className="font-semibold text-warn">Estado del contenido: </span>
      {REVIEW_STATUS}
      {extra ? ` ${extra}` : null}
    </p>
  );
}

/** Shown on an article only when its current wording was approved by a legal reviewer. */
export async function ProvisionReviewNotice({ path, versionId }: { path: string; versionId: string | null }) {
  const result = await fetchLatestReviews("constitution_provision", path);
  const state = reviewState(result.ok ? result.data[0] : undefined, versionId);
  if (state.kind !== "reviewed") return null;
  return (
    <p role="note" className="rounded border border-ok bg-surface p-4 text-sm">
      <span className="font-semibold text-ok">Revisión jurídica: </span>
      la presentación de este texto fue revisada por el equipo de revisión jurídica de NEXO el{" "}
      {formatDateTime(state.date)}. La vigencia debe comprobarse en la fuente oficial.
    </p>
  );
}

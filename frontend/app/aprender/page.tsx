import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { LessonReviewFallback, LessonReviewNotice } from "@/components/ReviewNotice";
import { LESSONS } from "@/lib/lessons";

export const metadata: Metadata = {
  title: "Aprender",
  description:
    "Rutas de aprendizaje sobre el Estado colombiano, con cada afirmación enlazada a la Constitución.",
};

export default function AprenderPage() {
  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          Academia
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">
          Primera ruta: el Estado y las leyes
        </h1>
        <p className="max-w-3xl text-lg text-ink-muted">
          Dos lecciones cortas para entender cómo está organizado el Estado
          colombiano y cómo se hace una ley. Cada afirmación indica qué tipo de
          afirmación es y enlaza al artículo de la Constitución en que se basa,
          para que pueda comprobarla.
        </p>
      </header>
      <Suspense fallback={<LessonReviewFallback />}>
        <LessonReviewNotice />
      </Suspense>
      <ol className="grid gap-4 sm:grid-cols-2">
        {LESSONS.map((lesson, index) => (
          <li
            key={lesson.slug}
            className="rounded border border-rule bg-surface p-5"
          >
            <p className="font-serif text-accent">Lección {index + 1}</p>
            <h2 className="mt-1 text-xl font-semibold">
              <Link
                href={`/aprender/${lesson.slug}`}
                className="text-brand underline underline-offset-4"
              >
                {lesson.title}
              </Link>
            </h2>
            <p className="mt-2 text-ink-muted">{lesson.summary}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}

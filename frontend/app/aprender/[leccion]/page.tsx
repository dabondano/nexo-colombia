import type { Metadata } from "next";
import Link from "next/link";
import { LessonReviewFallback, LessonReviewNotice } from "@/components/ReviewNotice";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { EPISTEMIC_LABELS } from "@/lib/format";
import {
  LESSONS,
  articlePath,
  type Lesson,
  type Statement,
} from "@/lib/lessons";

const EDITION_NOTE =
  "El texto de los artículos enlazados es el de una edición informativa; compruebe la vigencia en la fuente oficial.";

const linkClass = "text-brand underline underline-offset-4";

export function generateStaticParams() {
  return LESSONS.map((lesson) => ({ leccion: lesson.slug }));
}

export async function generateMetadata(
  props: PageProps<"/aprender/[leccion]">,
): Promise<Metadata> {
  const { leccion } = await props.params;
  const lesson = LESSONS.find((item) => item.slug === leccion);
  return {
    title: lesson ? lesson.title : "Lección",
    description: lesson?.summary,
  };
}

function Citations({ articles }: { articles: string[] }) {
  return (
    <span className="text-sm">
      Constitución,{" "}
      {articles.map((article, index) => (
        <span key={article}>
          {index > 0 ? ", " : null}
          <Link href={articlePath(article)} className={linkClass}>
            artículo {article}
          </Link>
        </span>
      ))}
    </span>
  );
}

function StatementItem({ statement }: { statement: Statement }) {
  const label = EPISTEMIC_LABELS[statement.label];
  return (
    <li className="border-t border-rule py-3 first:border-t-0">
      <p>{statement.text}</p>
      <p className="mt-1 text-ink-muted">
        <span
          className="mr-2 rounded border border-rule px-1.5 py-0.5 text-xs font-medium"
          title={label.meaning}
        >
          {label.name}
        </span>
        <Citations articles={statement.articles} />
      </p>
    </li>
  );
}

function LessonBody({ lesson }: { lesson: Lesson }) {
  const index = LESSONS.indexOf(lesson);
  const next = LESSONS[index + 1];
  return (
    <article className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          Academia · Lección {index + 1} de {LESSONS.length}
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">
          {lesson.title}
        </h1>
        <p className="max-w-3xl text-lg text-ink-muted">{lesson.summary}</p>
        <Suspense fallback={<LessonReviewFallback extra={EDITION_NOTE} />}>
          <LessonReviewNotice slug={lesson.slug} extra={EDITION_NOTE} />
        </Suspense>
      </header>

      {lesson.steps.map((step, stepIndex) => (
        <section key={step.heading} aria-labelledby={`paso-${stepIndex + 1}`}>
          <h2 id={`paso-${stepIndex + 1}`} className="text-xl font-semibold">
            {stepIndex + 1}. {step.heading}
          </h2>
          <ul className="mt-2 max-w-3xl">
            {step.statements.map((statement) => (
              <StatementItem key={statement.text} statement={statement} />
            ))}
          </ul>
        </section>
      ))}

      <section
        aria-labelledby="titulo-glosario"
        className="rounded border border-rule bg-surface p-5"
      >
        <h2 id="titulo-glosario" className="text-xl font-semibold">
          Glosario
        </h2>
        <dl className="mt-2">
          {lesson.glossary.map((term) => (
            <div
              key={term.term}
              className="border-t border-rule py-3 first:border-t-0"
            >
              <dt className="font-semibold">{term.term}</dt>
              <dd className="mt-1">
                {term.definition}
                <span className="mt-1 block text-ink-muted">
                  <span className="mr-2 rounded border border-rule px-1.5 py-0.5 text-xs font-medium">
                    {EPISTEMIC_LABELS.interpretacion_juridica.name}
                  </span>
                  <Citations articles={term.articles} />
                </span>
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="titulo-repaso" className="flex flex-col gap-3">
        <h2 id="titulo-repaso" className="text-xl font-semibold">
          Repaso
        </h2>
        <ol className="flex flex-col gap-4">
          {lesson.quiz.map((item, quizIndex) => (
            <li
              key={item.question}
              className="rounded border border-rule bg-surface p-5"
            >
              <p className="font-medium">
                {quizIndex + 1}. {item.question}
              </p>
              <ul className="mt-2 list-[upper-alpha] pl-6">
                {item.options.map((option) => (
                  <li key={option}>{option}</li>
                ))}
              </ul>
              <details className="mt-3">
                <summary className="cursor-pointer text-brand underline underline-offset-4">
                  Ver la respuesta
                </summary>
                <p className="mt-2">
                  <span className="font-semibold">
                    {String.fromCharCode(65 + item.answer)}.{" "}
                    {item.options[item.answer]}.
                  </span>{" "}
                  {item.explanation}
                </p>
                <p className="mt-1 text-ink-muted">
                  <Citations articles={item.articles} />
                </p>
              </details>
            </li>
          ))}
        </ol>
      </section>

      {lesson.related?.length ? (
        <section aria-labelledby="titulo-datos" className="flex flex-col gap-2">
          <h2 id="titulo-datos" className="text-xl font-semibold">
            Vea los datos
          </h2>
          <ul>
            {lesson.related.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className={linkClass}>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <nav
        aria-label="Lecciones"
        className="flex flex-wrap justify-between gap-4"
      >
        <Link href="/aprender" className={linkClass}>
          Todas las lecciones
        </Link>
        {next ? (
          <Link href={`/aprender/${next.slug}`} className={linkClass}>
            Siguiente lección: {next.title}
          </Link>
        ) : null}
      </nav>
    </article>
  );
}

async function LessonPage({
  params,
}: {
  params: Promise<{ leccion: string }>;
}) {
  const { leccion } = await params;
  const lesson = LESSONS.find((item) => item.slug === leccion);
  if (!lesson) notFound();
  return <LessonBody lesson={lesson} />;
}

export default function LeccionPage(props: PageProps<"/aprender/[leccion]">) {
  return (
    <Suspense fallback={<p role="status">Cargando la lección…</p>}>
      <LessonPage params={props.params} />
    </Suspense>
  );
}

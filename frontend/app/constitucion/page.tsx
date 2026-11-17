import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Notice } from "@/components/Notice";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import {
  CONSTITUTION_SLUG,
  fetchInstrument,
  type OutlineItem,
} from "@/lib/api";
import { formatNumber } from "@/lib/format";

export const metadata: Metadata = {
  title: "Constitución Política de 1991",
  description:
    "Texto de la Constitución Política de Colombia por títulos, capítulos y artículos, con su fuente.",
};

const linkClass = "text-brand underline underline-offset-4";

type Chapter = { item: OutlineItem; articles: OutlineItem[] };
type Title = {
  item: OutlineItem;
  articles: OutlineItem[];
  chapters: Chapter[];
};

/** The outline arrives in reading order; divisions come before what they contain. */
function buildTitles(outline: OutlineItem[]): Title[] {
  const titles: Title[] = [];
  for (const item of outline) {
    const title = titles.at(-1);
    if (item.kind === "titulo") {
      titles.push({ item, articles: [], chapters: [] });
    } else if (item.kind === "capitulo" && title) {
      title.chapters.push({ item, articles: [] });
    } else if (item.kind === "articulo" && title) {
      const chapter = title.chapters.at(-1);
      (chapter && item.parent_id === chapter.item.id
        ? chapter.articles
        : title.articles
      ).push(item);
    }
  }
  return titles;
}

function Articles({ articles }: { articles: OutlineItem[] }) {
  if (articles.length === 0) return null;
  return (
    <ul className="mt-2 flex flex-col">
      {articles.map((article) => (
        <li key={article.id} className="border-t border-rule py-2">
          <Link
            href={`/constitucion/${article.path}`}
            className={`${linkClass} font-medium`}
          >
            {article.label}
          </Link>
          {article.data_quality_status === "incomplete" ? (
            <span className="ml-2 rounded border border-warn px-1.5 py-0.5 text-xs text-warn">
              Requiere revisión
            </span>
          ) : null}
          {article.excerpt ? (
            <span className="block text-sm text-ink-muted">
              {article.excerpt}
            </span>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

function heading(item: OutlineItem): string {
  return item.heading ? `${item.label}. ${item.heading}` : item.label;
}

async function Outline() {
  const result = await fetchInstrument(CONSTITUTION_SLUG);
  if (!result.ok) {
    return (
      <Notice>
        {result.notFound
          ? "El texto de la Constitución todavía no está cargado en NEXO."
          : `${result.reason} El texto no está disponible en este momento.`}
      </Notice>
    );
  }
  const constitution = result.data;
  const titles = buildTitles(constitution.outline);
  const preamble = constitution.outline.find(
    (item) => item.kind === "preambulo",
  );

  return (
    <>
      <section
        aria-labelledby="titulo-edicion"
        className="rounded border border-warn bg-surface p-5"
      >
        <h2 id="titulo-edicion" className="text-xl font-semibold">
          Qué edición es esta
        </h2>
        <p className="mt-2">{constitution.edition_note}</p>
        <p className="mt-2">
          Hay {formatNumber(constitution.article_count)} artículos cargados. En{" "}
          {formatNumber(constitution.articles_needing_review)} de ellos la
          fuente mezcla el texto vigente con texto anterior o tachado, o no
          imprime texto: aparecen marcados con «Requiere revisión» y deben
          leerse junto con la fuente oficial.
        </p>
      </section>

      <nav
        aria-labelledby="titulo-indice"
        className="rounded border border-rule bg-surface p-5"
      >
        <h2 id="titulo-indice" className="text-xl font-semibold">
          Índice
        </h2>
        <ul className="mt-2 flex flex-col gap-1">
          {preamble ? (
            <li>
              <Link
                href={`/constitucion/${preamble.path}`}
                className={linkClass}
              >
                Preámbulo
              </Link>
            </li>
          ) : null}
          {titles.map((title) => (
            <li key={title.item.id}>
              <a href={`#${title.item.path}`} className={linkClass}>
                {heading(title.item)}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      {titles.map((title) => (
        <section
          key={title.item.id}
          aria-labelledby={title.item.path}
          className="scroll-mt-4"
        >
          <h2
            id={title.item.path}
            className="font-serif text-2xl font-semibold text-brand"
          >
            {heading(title.item)}
          </h2>
          <Articles articles={title.articles} />
          {title.chapters.map((chapter) => (
            <div key={chapter.item.id} className="mt-5">
              <h3 className="text-lg font-semibold">{heading(chapter.item)}</h3>
              <Articles articles={chapter.articles} />
            </div>
          ))}
        </section>
      ))}

      <ProvenancePanel
        provenance={constitution.provenance}
        epistemicLabel="hecho_documentado"
        dataQualityStatus="acceptable"
        qualityMeaning="El texto se muestra tal como lo publica la fuente, que es una edición informativa."
      />
    </>
  );
}

export default function ConstitucionPage() {
  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          Norma
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">
          Constitución Política de Colombia de 1991
        </h1>
        <p className="max-w-3xl text-lg text-ink-muted">
          El texto permanente de la Constitución, por títulos, capítulos y
          artículos, tal como lo publica Función Pública. Los encabezados y la
          ortografía son los de la fuente.
        </p>
      </header>
      <Suspense fallback={<p role="status">Cargando la Constitución…</p>}>
        <Outline />
      </Suspense>
    </div>
  );
}

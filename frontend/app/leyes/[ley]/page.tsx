import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Notice } from "@/components/Notice";
import { ProvenancePanel } from "@/components/ProvenancePanel";
import { fetchInstrument, lawName, type OutlineItem } from "@/lib/api";
import { formatCalendarDate, formatNumber } from "@/lib/format";

const linkClass = "text-brand underline underline-offset-4";

export async function generateMetadata(props: PageProps<"/leyes/[ley]">): Promise<Metadata> {
  const { ley } = await props.params;
  const result = await fetchInstrument(ley);
  return { title: result.ok ? lawName(result.data) : "Norma" };
}

type Node = { item: OutlineItem; children: Node[] };

/** Divisions and articles as a tree; the outline arrives in reading order. */
function buildTree(outline: OutlineItem[]): Node[] {
  const nodes = new Map<string, Node>();
  const roots: Node[] = [];
  for (const item of outline) {
    const node: Node = { item, children: [] };
    nodes.set(item.id, node);
    const parent = item.parent_id ? nodes.get(item.parent_id) : undefined;
    (parent ? parent.children : roots).push(node);
  }
  return roots;
}

/** Divisions are anchors of the index: "titulo-i", "estatuto-capitulo-ii". */
function anchor(item: OutlineItem): string {
  return item.path.replaceAll("/", "-");
}

function heading(item: OutlineItem): string {
  return item.heading ? `${item.label}. ${item.heading}` : item.label;
}

function Article({ item, slug }: { item: OutlineItem; slug: string }) {
  return (
    <li className="border-t border-rule py-2">
      <Link href={`/leyes/${slug}/${item.path}`} className={`${linkClass} font-medium`}>
        {item.label}
      </Link>
      {item.data_quality_status === "incomplete" ? (
        <span className="ml-2 rounded border border-warn px-1.5 py-0.5 text-xs text-warn">
          Requiere revisión
        </span>
      ) : null}
      {item.excerpt ? <span className="block text-sm text-ink-muted">{item.excerpt}</span> : null}
    </li>
  );
}

function Division({ node, slug, depth }: { node: Node; slug: string; depth: number }) {
  const articles = node.children.filter((child) => child.item.kind === "articulo");
  const divisions = node.children.filter((child) => child.item.kind !== "articulo");
  const Heading = depth === 0 ? "h2" : depth === 1 ? "h3" : "h4";
  const size = depth === 0 ? "font-serif text-2xl text-brand" : depth === 1 ? "text-lg" : "text-base";
  // Top-level divisions and their children are anchors of the index.
  const id = depth <= 1 ? anchor(node.item) : `division-${node.item.id}`;
  return (
    <section aria-labelledby={id} className={depth === 0 ? "scroll-mt-4" : "mt-4"}>
      <Heading id={id} className={`font-semibold ${size}`}>
        {heading(node.item)}
      </Heading>
      {articles.length > 0 ? (
        <ul className="mt-2 flex flex-col">
          {articles.map((child) => (
            <Article key={child.item.id} item={child.item} slug={slug} />
          ))}
        </ul>
      ) : null}
      {divisions.map((child) => (
        <div key={child.item.id} className={depth < 2 ? "pl-0 sm:pl-4" : ""}>
          <Division node={child} slug={slug} depth={depth + 1} />
        </div>
      ))}
    </section>
  );
}

async function Outline({ params }: { params: Promise<{ ley: string }> }) {
  const { ley } = await params;
  const result = await fetchInstrument(ley);
  if (!result.ok) {
    if (result.notFound) notFound();
    return <Notice>{result.reason} Esta ley no está disponible en este momento.</Notice>;
  }
  const law = result.data;
  const tree = buildTree(law.outline);
  const loose = tree.filter((node) => node.item.kind === "articulo");
  const divisions = tree.filter((node) => node.item.kind !== "articulo");
  const summary = law.title.replace(`${lawName(law)}, `, "");
  // One top-level division (a compiled statute): index its divisions instead.
  const indexed =
    divisions.length === 1
      ? divisions[0].children.filter((node) => node.item.kind !== "articulo")
      : divisions;

  return (
    <>
      <header className="flex flex-col gap-3">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">
          {law.instrument_type}
        </p>
        <h1 className="font-serif text-3xl font-semibold text-brand">{lawName(law)}</h1>
        <p className="max-w-3xl text-lg">{summary}</p>
        <p className="text-sm text-ink-muted">
          {[
            law.promulgated_on
              ? `${law.instrument_type === "decreto" ? "Expedido" : "Expedida"} el ${formatCalendarDate(law.promulgated_on)}`
              : null,
            law.official_publication_ref,
          ]
            .filter(Boolean)
            .join(" · ")}
        </p>
      </header>

      <section aria-labelledby="titulo-edicion" className="rounded border border-warn bg-surface p-5">
        <h2 id="titulo-edicion" className="text-xl font-semibold">
          Qué edición es esta
        </h2>
        <p className="mt-2">{law.edition_note}</p>
        <p className="mt-2">
          Hay {formatNumber(law.article_count)} artículos cargados.
          {law.articles_needing_review > 0
            ? ` En ${formatNumber(law.articles_needing_review)} de ellos la fuente mezcla el texto vigente con texto anterior o tachado, o no imprime texto: aparecen marcados con «Requiere revisión».`
            : ""}
        </p>
      </section>

      {indexed.length > 1 ? (
        <nav aria-labelledby="titulo-indice" className="rounded border border-rule bg-surface p-5">
          <h2 id="titulo-indice" className="text-xl font-semibold">
            Índice
          </h2>
          <ul className="mt-2 flex flex-col gap-1">
            {indexed.map((node) => (
              <li key={node.item.id}>
                <a href={`#${anchor(node.item)}`} className={linkClass}>
                  {heading(node.item)}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}

      {loose.length > 0 ? (
        <section aria-label="Artículos">
          <ul className="flex flex-col">
            {loose.map((node) => (
              <Article key={node.item.id} item={node.item} slug={law.slug} />
            ))}
          </ul>
        </section>
      ) : null}
      {divisions.map((node) => (
        <Division key={node.item.id} node={node} slug={law.slug} depth={0} />
      ))}

      <ProvenancePanel
        provenance={law.provenance}
        epistemicLabel="hecho_documentado"
        dataQualityStatus="acceptable"
        qualityMeaning="El texto se muestra tal como lo publica la fuente, que es una edición informativa."
      />
    </>
  );
}

export default function LeyPage(props: PageProps<"/leyes/[ley]">) {
  return (
    <div className="flex flex-col gap-8">
      <nav aria-label="Ruta de navegación">
        <Link href="/leyes" className={linkClass}>
          Volver a las leyes
        </Link>
      </nav>
      <Suspense fallback={<p role="status">Cargando la ley…</p>}>
        <Outline params={props.params} />
      </Suspense>
    </div>
  );
}

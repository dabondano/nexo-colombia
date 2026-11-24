import { Notice } from "@/components/Notice";
import { SourceText, hasStruckText } from "@/components/SourceText";
import type { Provision, Segment } from "@/lib/api";

/** How a provision's wording is shown: notes, wording after "TEXTO ANTERIOR", struck words. */
export function SegmentBlock({ segment }: { segment: Segment }) {
  if (segment.kind === "note") {
    return (
      <p className="border-l-4 border-rule pl-3 text-sm text-ink-muted">
        <span className="font-medium">Nota de la fuente: </span>
        {segment.text}
      </p>
    );
  }
  if (segment.kind === "after_previous_mark") {
    return (
      <p className="border-l-4 border-warn pl-3 text-ink-muted">
        <span className="block text-sm font-medium text-warn">
          Impreso después de la marca «TEXTO ANTERIOR»: puede no estar vigente
        </span>
        <SourceText text={segment.text} />
      </p>
    );
  }
  return (
    <p className="text-lg leading-relaxed">
      <SourceText text={segment.text} />
    </p>
  );
}

export function ReviewWarning({ provision }: { provision: Provision }) {
  const afterMark = provision.segments.some(
    (s) => s.kind === "after_previous_mark",
  );
  const struck = provision.segments.some((s) => hasStruckText(s.text));
  const noWording = !provision.segments.some((s) => s.kind === "text");
  if (!afterMark && !struck && !noWording) return null;
  return (
    <section
      aria-labelledby="titulo-revision"
      className="rounded border border-warn bg-surface p-5"
    >
      <h2 id="titulo-revision" className="text-lg font-semibold text-warn">
        Este artículo requiere revisión con la fuente oficial
      </h2>
      <ul className="mt-2 list-disc pl-5">
        {afterMark ? (
          <li>
            La fuente imprime texto después de su marca «TEXTO ANTERIOR» y no
            indica dónde termina el texto anterior. Lo que aparece después de
            esa marca puede incluir texto que ya no está vigente y también
            incisos vigentes.
          </li>
        ) : null}
        {struck ? (
          <li>
            La fuente muestra palabras tachadas. Aquí aparecen tachadas y no se
            buscan.
          </li>
        ) : null}
        {noWording ? (
          <li>La fuente no imprime texto vigente para este artículo.</li>
        ) : null}
      </ul>
    </section>
  );
}


export function ProvisionText({ segments }: { segments: Segment[] }) {
  if (segments.length === 0) {
    return <Notice>La fuente no imprime texto para esta parte.</Notice>;
  }
  return (
    <>
      {segments.map((segment, index) => (
        <SegmentBlock key={index} segment={segment} />
      ))}
    </>
  );
}

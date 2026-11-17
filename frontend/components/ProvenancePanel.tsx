import type { Provenance } from "@/lib/api";
import { EPISTEMIC_LABELS, QUALITY_LABELS, formatDateTime } from "@/lib/format";

type Props = {
  provenance: Provenance;
  epistemicLabel: string;
  dataQualityStatus: string;
  /** Replaces the general meaning of the quality status when a record type has its own criterion. */
  qualityMeaning?: string;
};

function Row({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-x-4 gap-y-1 border-t border-rule py-2 sm:grid-cols-[14rem_1fr]">
      <dt className="font-medium">{term}</dt>
      <dd className="text-ink-muted">{children}</dd>
    </div>
  );
}

const linkClass = "text-brand underline underline-offset-4";

/** "Where does this come from?": shown on every record page (PRD FR-PLT-03). */
export function ProvenancePanel({
  provenance,
  epistemicLabel,
  dataQualityStatus,
  qualityMeaning,
}: Props) {
  const label = EPISTEMIC_LABELS[epistemicLabel] ?? EPISTEMIC_LABELS.no_verificado;
  const quality = QUALITY_LABELS[dataQualityStatus];
  const sourceVerified = provenance.source_verification_status === "verified";

  return (
    <section aria-labelledby="titulo-origen" className="rounded border border-rule bg-surface p-5">
      <h2 id="titulo-origen" className="text-xl font-semibold">
        Origen de este registro
      </h2>
      <dl className="mt-3 text-sm">
        <Row term="Tipo de afirmación">
          <span className="font-medium text-ink">{label.name}.</span> {label.meaning}
        </Row>
        <Row term="Fuente">
          <a href={provenance.source_url} className={linkClass} rel="noopener noreferrer">
            {provenance.source_name}
          </a>
          , {provenance.source_institution}.{" "}
          {sourceVerified ? "Fuente verificada." : "Fuente aún sin verificar."}
        </Row>
        {provenance.original_url && provenance.original_url !== provenance.source_url ? (
          <Row term="Registro en la fuente">
            <a
              href={provenance.original_url}
              className={`${linkClass} break-all`}
              rel="noopener noreferrer"
            >
              {provenance.original_url}
            </a>
          </Row>
        ) : null}
        <Row term="Obtenido por NEXO">{formatDateTime(provenance.acquired_at)}</Row>
        <Row term="Actualizado en la fuente">{formatDateTime(provenance.published_at)}</Row>
        <Row term="Última verificación">{formatDateTime(provenance.last_verified_at)}</Row>
        <Row term="Calidad del registro">
          {quality ? (
            <>
              <span className="font-medium text-ink">{quality.name}.</span>{" "}
              {qualityMeaning ?? quality.meaning}
            </>
          ) : (
            dataQualityStatus
          )}{" "}
          Esta calificación describe el registro, no a la entidad ni a las personas.
        </Row>
        {provenance.processing_notes.length > 0 ? (
          <Row term="Ajustes hechos por NEXO">
            {provenance.processing_notes.map((note) => (
              <span key={note} className="block">
                {note}
              </span>
            ))}
          </Row>
        ) : null}
        <Row term="Licencia de los datos">{provenance.licence ?? "No indicada"}</Row>
      </dl>
    </section>
  );
}

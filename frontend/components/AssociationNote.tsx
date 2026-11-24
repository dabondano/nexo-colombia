import { EPISTEMIC_LABELS } from "@/lib/format";

/** Explains a link that NEXO computed, as opposed to one the source states. */
export function AssociationNote({ label, rule }: { label: string; rule: string }) {
  const epistemic = EPISTEMIC_LABELS[label] ?? EPISTEMIC_LABELS.no_verificado;
  return (
    <p className="mt-4 border-l-4 border-rule pl-3 text-sm text-ink-muted">
      <span className="font-medium text-ink">Tipo de afirmación: {epistemic.name}.</span>{" "}
      {rule}
    </p>
  );
}

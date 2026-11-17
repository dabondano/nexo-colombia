import type { Stage } from "@/lib/modules";

export function StageBadge({ stage }: { stage: Stage }) {
  return (
    <span className="inline-block rounded border border-rule bg-paper px-2 py-0.5 text-xs font-medium text-ink-muted">
      <span className="sr-only">Estado de avance: </span>
      {stage}
    </span>
  );
}

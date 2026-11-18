import type { BudgetAmounts, BudgetRates } from "@/lib/api";
import { formatPesos, formatPesosShort, formatRate } from "@/lib/format";

const STAGES: { key: keyof BudgetAmounts; label: string; rate?: keyof BudgetRates }[] = [
  { key: "appropriation", label: "Apropiación vigente" },
  { key: "commitments", label: "Compromisos", rate: "commitments" },
  { key: "obligations", label: "Obligaciones", rate: "obligations" },
  { key: "payments", label: "Pagos", rate: "payments" },
];

/** The four published amounts with their share of the appropriation. */
export function BudgetFigures({ amounts, rates }: { amounts: BudgetAmounts; rates: BudgetRates }) {
  return (
    <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {STAGES.map((stage) => (
        <div key={stage.key} className="rounded border border-rule bg-surface p-4">
          <dt className="text-sm font-medium">{stage.label}</dt>
          <dd className="mt-1">
            <span className="block text-xl font-semibold">{formatPesosShort(amounts[stage.key])}</span>
            <span className="block text-sm text-ink-muted">{formatPesos(amounts[stage.key])}</span>
            {stage.rate ? (
              <span className="mt-1 block text-sm">
                {formatRate(rates[stage.rate])} de la apropiación
              </span>
            ) : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function BudgetNotes({ yearNote, formula }: { yearNote: string; formula: string }) {
  return (
    <div className="flex flex-col gap-2 rounded border border-rule bg-surface p-4 text-sm">
      <p>
        <span className="font-semibold">Periodo de las cifras: </span>
        {yearNote}
      </p>
      <p>
        <span className="font-semibold">Cómo se calculan los porcentajes: </span>
        {formula}
      </p>
      <p className="text-ink-muted">
        CSF y SSF son las abreviaturas que usa la fuente para «con situación de fondos» y «sin
        situación de fondos». Los porcentajes describen el avance de la ejecución según la fuente;
        no califican la gestión de ninguna entidad.
      </p>
    </div>
  );
}

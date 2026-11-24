import type { Metadata } from "next";
import { Suspense } from "react";
import { Notice } from "@/components/Notice";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { formatNumber, QUALITY_LABELS } from "@/lib/format";
import { STATUS_LABELS } from "@/lib/staff-labels";
import { formatTimestamp, requireStaff, staffRequest, type SourceQuality } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Calidad de los datos",
  robots: { index: false, follow: false },
};

const QUALITY_ORDER = ["verified", "acceptable", "incomplete", "conflicting", "stale"];

function SourceCard({ item }: { item: SourceQuality }) {
  const headingId = `fuente-${item.source_id}`;
  const total = Object.values(item.records_by_quality).reduce((sum, n) => sum + n, 0);
  return (
    <li>
      <section aria-labelledby={headingId} className="rounded border border-rule bg-surface p-5">
        <h2 id={headingId} className="text-xl font-semibold">
          {item.name}
        </h2>
        {item.checks.length > 0 ? (
          <div className="mt-3 border-l-4 border-warn pl-3">
            <p className="font-medium">Para revisar</p>
            <ul className="mt-1 list-disc pl-5 text-sm">
              {item.checks.map((check) => (
                <li key={check}>{check}</li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="mt-3 text-sm">Sin avisos.</p>
        )}
        <dl className="mt-3 grid gap-x-4 gap-y-1 text-sm sm:grid-cols-[16rem_1fr]">
          <dt className="font-medium">Última sincronización</dt>
          <dd>
            {formatTimestamp(item.last_run.started_at)} ·{" "}
            {STATUS_LABELS[item.last_run.status] ?? item.last_run.status} ·{" "}
            {formatNumber(item.last_run.rows_seen)} filas vistas,{" "}
            {formatNumber(item.last_run.rows_rejected)} rechazadas
          </dd>
          <dt className="font-medium">Última carga correcta</dt>
          <dd>{item.last_success_at ? formatTimestamp(item.last_success_at) : "Ninguna"}</dd>
          <dt className="font-medium">Última actualización del publicador</dt>
          <dd>
            {item.source_updated_at
              ? formatTimestamp(item.source_updated_at)
              : "La fuente no la indica"}
          </dd>
          <dt className="font-medium">Registros publicados</dt>
          <dd>
            {total === 0
              ? "Ninguno"
              : QUALITY_ORDER.filter((status) => item.records_by_quality[status])
                  .map(
                    (status) =>
                      `${formatNumber(item.records_by_quality[status])} ${(
                        QUALITY_LABELS[status]?.name ?? status
                      ).toLowerCase()}`,
                  )
                  .join(" · ")}
          </dd>
        </dl>
      </section>
    </li>
  );
}

async function Quality() {
  const { user, allowed } = await requireStaff(["data_steward"]);
  if (!allowed) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Calidad de los datos" />
        <Forbidden />
      </div>
    );
  }
  const result = await staffRequest<SourceQuality[]>("/admin/data-quality");
  const flagged = result.ok ? result.data.filter((item) => item.checks.length > 0).length : 0;
  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Calidad de los datos" />
      <p className="max-w-3xl text-sm text-ink-muted">
        Una ficha por fuente cargada. Los avisos comparan cada carga con la anterior que terminó
        bien: menos filas que antes (más de un 10 %), más filas rechazadas, una carga fallida o
        ninguna carga correcta en más de 8 días (la sincronización programada es semanal). Los
        estados de calidad califican registros, nunca personas ni entidades.
      </p>
      {!result.ok ? (
        <Notice>{result.reason}</Notice>
      ) : result.data.length === 0 ? (
        <Notice>Todavía no se ha cargado ninguna fuente.</Notice>
      ) : (
        <>
          <p role="status" className="font-medium">
            {flagged === 0
              ? "Ninguna fuente tiene avisos."
              : `${flagged} ${flagged === 1 ? "fuente tiene avisos" : "fuentes tienen avisos"}.`}
          </p>
          <ul className="flex flex-col gap-4">
            {result.data.map((item) => (
              <SourceCard key={item.source_id} item={item} />
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

export default function CalidadPage() {
  return (
    <Suspense fallback={<p role="status">Cargando…</p>}>
      <Quality />
    </Suspense>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import { ScrollRegion } from "@/components/ScrollRegion";
import { formatNumber, pageNumber, type SearchParams } from "@/lib/format";
import { STATUS_LABELS } from "@/lib/staff-labels";
import { formatTimestamp, requireStaff, staffRequest, type SyncRun } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Sincronizaciones",
  robots: { index: false, follow: false },
};

const PAGE_SIZE = 25;
const BASE_PATH = "/panel/sincronizaciones";

async function Runs({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const { user, allowed } = await requireStaff(["data_steward"]);
  if (!allowed) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Sincronizaciones" />
        <Forbidden />
      </div>
    );
  }
  const page = pageNumber(await searchParams);
  const result = await staffRequest<{ total: number; items: SyncRun[] }>("/admin/sync-runs", {
    params: { limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE },
  });
  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Sincronizaciones" />
      <p className="max-w-3xl text-sm text-ink-muted">
        Cada carga de una fuente, de la más reciente a la más antigua. Las cargas se inician hoy
        desde la línea de comandos (<code>python -m app.ingestion.cli all</code>).
      </p>
      {!result.ok ? (
        <Notice>{result.reason}</Notice>
      ) : result.data.total === 0 ? (
        <Notice>Todavía no hay sincronizaciones registradas.</Notice>
      ) : (
        <ScrollRegion label="Tabla de sincronizaciones" className="rounded border border-rule bg-surface">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Sincronizaciones de datos</caption>
            <thead>
              <tr className="border-b border-rule">
                <th scope="col" className="p-3">Fuente</th>
                <th scope="col" className="p-3">Inicio</th>
                <th scope="col" className="p-3">Estado</th>
                <th scope="col" className="p-3 text-right">Vistas</th>
                <th scope="col" className="p-3 text-right">Nuevas</th>
                <th scope="col" className="p-3 text-right">Modificadas</th>
                <th scope="col" className="p-3 text-right">Rechazadas</th>
              </tr>
            </thead>
            <tbody>
              {result.data.items.map((run) => (
                <tr key={run.id} className="border-t border-rule align-top">
                  <th scope="row" className="p-3 font-normal">
                    {run.source_name}
                  </th>
                  <td className="p-3">{formatTimestamp(run.started_at)}</td>
                  <td className="p-3">
                    {STATUS_LABELS[run.status] ?? run.status}
                    {run.error ? <span className="block text-warn">{run.error}</span> : null}
                  </td>
                  <td className="p-3 text-right">{formatNumber(run.rows_seen)}</td>
                  <td className="p-3 text-right">{formatNumber(run.rows_new)}</td>
                  <td className="p-3 text-right">{formatNumber(run.rows_changed)}</td>
                  <td className="p-3 text-right">
                    {run.rows_rejected > 0 ? (
                      <Link
                        href={`${BASE_PATH}/${run.id}`}
                        className="text-brand underline underline-offset-4"
                        aria-label={`${formatNumber(run.rows_rejected)} filas rechazadas de ${run.source_name}: ver motivos`}
                      >
                        {formatNumber(run.rows_rejected)}
                      </Link>
                    ) : (
                      "0"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollRegion>
      )}
      {result.ok ? (
        <Pagination basePath={BASE_PATH} query={{}} page={page} pageSize={PAGE_SIZE} total={result.data.total} />
      ) : null}
    </div>
  );
}

export default function SincronizacionesPage(props: PageProps<"/panel/sincronizaciones">) {
  return (
    <Suspense fallback={<p role="status">Cargando las sincronizaciones…</p>}>
      <Runs searchParams={props.searchParams} />
    </Suspense>
  );
}

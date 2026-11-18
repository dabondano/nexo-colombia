import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import { formatNumber, pageNumber, type SearchParams } from "@/lib/format";
import { STATUS_LABELS } from "@/lib/staff-labels";
import { formatTimestamp, requireStaff, staffRequest, type SyncRun } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Filas rechazadas",
  robots: { index: false, follow: false },
};

const PAGE_SIZE = 25;

type RejectPage = {
  run: SyncRun;
  total: number;
  items: { id: string; external_id: string | null; reason: string; payload: Record<string, unknown> }[];
};

async function Rejects({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { user, allowed } = await requireStaff(["data_steward"]);
  if (!allowed) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Filas rechazadas" />
        <Forbidden />
      </div>
    );
  }
  const { id } = await params;
  const page = pageNumber(await searchParams);
  const result = await staffRequest<RejectPage>(
    `/admin/sync-runs/${encodeURIComponent(id)}/rejects`,
    { params: { limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE } },
  );
  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Filas rechazadas" />
      <Link href="/panel/sincronizaciones" className="text-brand underline underline-offset-4">
        Volver a las sincronizaciones
      </Link>
      {!result.ok ? (
        <Notice>{result.reason}</Notice>
      ) : (
        <>
          <p className="text-sm text-ink-muted">
            {result.data.run.source_name} · {formatTimestamp(result.data.run.started_at)} ·{" "}
            {STATUS_LABELS[result.data.run.status] ?? result.data.run.status} ·{" "}
            {formatNumber(result.data.total)} filas rechazadas. Cada fila se muestra tal como la
            publicó la fuente, con el motivo del rechazo.
          </p>
          <ul className="flex flex-col gap-4">
            {result.data.items.map((reject) => (
              <li key={reject.id} className="rounded border border-rule bg-surface p-5 text-sm">
                <p className="font-medium">{reject.reason}</p>
                <p className="mt-1 text-ink-muted">
                  Identificador en la fuente: {reject.external_id ?? "sin identificador"}
                </p>
                <details className="mt-2">
                  <summary className="cursor-pointer text-brand">Ver la fila publicada</summary>
                  <pre className="mt-2 overflow-x-auto rounded bg-paper p-3 text-xs">
                    {JSON.stringify(reject.payload, null, 2)}
                  </pre>
                </details>
              </li>
            ))}
          </ul>
          <Pagination
            basePath={`/panel/sincronizaciones/${id}`}
            query={{}}
            page={page}
            pageSize={PAGE_SIZE}
            total={result.data.total}
          />
        </>
      )}
    </div>
  );
}

export default function RechazosPage(props: PageProps<"/panel/sincronizaciones/[id]">) {
  return (
    <Suspense fallback={<p role="status">Cargando las filas rechazadas…</p>}>
      <Rejects params={props.params} searchParams={props.searchParams} />
    </Suspense>
  );
}

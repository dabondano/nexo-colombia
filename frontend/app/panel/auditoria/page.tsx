import type { Metadata } from "next";
import { Suspense } from "react";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import { formatNumber, pageNumber, param, type SearchParams } from "@/lib/format";
import { AUDIT_ACTIONS } from "@/lib/staff-labels";
import { formatTimestamp, requireStaff, staffRequest } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Registro de auditoría",
  robots: { index: false, follow: false },
};

const PAGE_SIZE = 50;
const BASE_PATH = "/panel/auditoria";

type AuditEvent = {
  id: string;
  occurred_at: string;
  actor_email: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  details: Record<string, unknown>;
};

function describe(details: Record<string, unknown>): string {
  return Object.entries(details)
    .map(([key, value]) => `${key}: ${typeof value === "object" ? JSON.stringify(value) : String(value)}`)
    .join(" · ");
}

async function Log({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const { user, allowed } = await requireStaff(["admin"]);
  if (!allowed) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Registro de auditoría" />
        <Forbidden />
      </div>
    );
  }
  const query = await searchParams;
  const action = param(query, "accion");
  const page = pageNumber(query);
  const result = await staffRequest<{ total: number; items: AuditEvent[] }>("/admin/audit", {
    params: { action, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE },
  });
  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Registro de auditoría" />
      <p className="max-w-3xl text-sm text-ink-muted">
        Registro de solo adición: la base de datos rechaza cualquier cambio o borrado. No guarda
        direcciones IP ni datos del navegador.
      </p>
      <form action={BASE_PATH} method="get" className="flex flex-wrap items-end gap-3 rounded border border-rule bg-surface p-4">
        <div className="flex flex-col gap-1">
          <label htmlFor="filtro-accion" className="text-sm font-medium">
            Acción
          </label>
          <select
            id="filtro-accion"
            name="accion"
            defaultValue={action ?? ""}
            className="rounded border border-rule bg-surface px-3 py-2 text-base"
          >
            <option value="">Todas</option>
            {Object.entries(AUDIT_ACTIONS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" className="rounded bg-brand px-5 py-2 font-medium text-brand-ink">
          Filtrar
        </button>
      </form>
      {!result.ok ? (
        <Notice>{result.reason}</Notice>
      ) : result.data.total === 0 ? (
        <Notice>No hay eventos registrados{action ? " para esta acción" : ""}.</Notice>
      ) : (
        <>
          <p role="status" className="text-sm">
            {formatNumber(result.data.total)} eventos, del más reciente al más antiguo.
          </p>
          <ul className="flex flex-col gap-2">
            {result.data.items.map((event) => (
              <li key={event.id} className="rounded border border-rule bg-surface p-4 text-sm">
                <p>
                  <span className="font-medium">{AUDIT_ACTIONS[event.action] ?? event.action}</span> ·{" "}
                  {formatTimestamp(event.occurred_at)} ·{" "}
                  {event.actor_email ?? "Sistema o línea de comandos"}
                </p>
                {Object.keys(event.details).length > 0 || event.target_id ? (
                  <p className="mt-1 break-words text-ink-muted">
                    {[event.target_type && event.target_id ? `${event.target_type} ${event.target_id}` : null, describe(event.details) || null]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
          <Pagination basePath={BASE_PATH} query={{ accion: action }} page={page} pageSize={PAGE_SIZE} total={result.data.total} />
        </>
      )}
    </div>
  );
}

export default function AuditoriaPage(props: PageProps<"/panel/auditoria">) {
  return (
    <Suspense fallback={<p role="status">Cargando el registro…</p>}>
      <Log searchParams={props.searchParams} />
    </Suspense>
  );
}

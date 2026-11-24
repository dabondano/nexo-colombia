import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { FilterForm, TextFilter } from "@/components/Filters";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { DeleteMappingForm } from "@/components/StaffForms";
import { formatNumber, pageNumber, param, type SearchParams } from "@/lib/format";
import { formatTimestamp, requireStaff, staffRequest } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Vínculos entre fuentes",
  robots: { index: false, follow: false },
};

const PAGE_SIZE = 25;
const BASE_PATH = "/panel/vinculos";
const linkClass = "text-brand underline underline-offset-4";

const KINDS = {
  budget_entity: { label: "Presupuesto", records: "líneas de presupuesto" },
  contract_entity: { label: "Contratos", records: "contratos" },
} as const;
type Kind = keyof typeof KINDS;

type Candidate = {
  kind: Kind;
  source_value: string;
  source_name: string;
  detail: string | null;
  records: number;
  reason: string;
};
type Mapping = {
  id: string;
  kind: Kind;
  source_name: string;
  institution_id: string;
  institution_name: string;
  note: string;
  created_by_email: string | null;
  created_at: string;
};

function newHref(item: Candidate): string {
  const params = new URLSearchParams({
    tipo: item.kind,
    valor: item.source_value,
    nombre: item.source_name,
  });
  return `${BASE_PATH}/nuevo?${params.toString()}`;
}

async function Links({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const { user, allowed } = await requireStaff(["data_steward"]);
  if (!allowed) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Vínculos entre fuentes" />
        <Forbidden />
      </div>
    );
  }
  const query = await searchParams;
  const kind: Kind = param(query, "tipo") === "contract_entity" ? "contract_entity" : "budget_entity";
  const q = param(query, "q");
  const page = pageNumber(query);
  const [pending, mappings] = await Promise.all([
    staffRequest<{ total: number; items: Candidate[] }>("/admin/entity-mappings/candidates", {
      params: { kind, q, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE },
    }),
    staffRequest<Mapping[]>("/admin/entity-mappings"),
  ]);
  const reviewed = mappings.ok ? mappings.data.filter((item) => item.kind === kind) : [];

  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Vínculos entre fuentes" />
      <p className="max-w-3xl text-sm text-ink-muted">
        Las reglas automáticas solo enlazan una entidad del presupuesto o de SECOP con el
        directorio cuando el nombre (presupuesto) o el NIT (contratos) coincide con una sola
        entidad. Aquí puede enlazar a mano las que quedan pendientes, con el motivo. El vínculo
        se aplica de inmediato, se muestra en las páginas como revisado por el equipo y queda en
        la auditoría.
      </p>
      {param(query, "creado") ? (
        <p role="status" className="border-l-4 border-brand pl-3">
          Vínculo guardado y aplicado.
        </p>
      ) : param(query, "eliminado") ? (
        <p role="status" className="border-l-4 border-brand pl-3">
          Vínculo eliminado. La entidad vuelve a la lista de pendientes.
        </p>
      ) : null}
      <nav aria-label="Fuente" className="flex gap-4">
        {(Object.keys(KINDS) as Kind[]).map((option) => (
          <Link
            key={option}
            href={`${BASE_PATH}?tipo=${option}`}
            aria-current={option === kind ? "page" : undefined}
            className={`${linkClass} ${option === kind ? "font-semibold" : ""}`}
          >
            {KINDS[option].label}
          </Link>
        ))}
      </nav>

      <section aria-labelledby="titulo-revisados" className="flex flex-col gap-3">
        <h2 id="titulo-revisados" className="text-xl font-semibold">
          Vínculos revisados ({formatNumber(reviewed.length)})
        </h2>
        {!mappings.ok ? (
          <Notice>{mappings.reason}</Notice>
        ) : reviewed.length === 0 ? (
          <p className="text-sm">Todavía no hay vínculos revisados para esta fuente.</p>
        ) : (
          <ul className="rounded border border-rule bg-surface px-5">
            {reviewed.map((item) => (
              <li key={item.id} className="flex flex-col gap-2 border-t border-rule py-4 first:border-t-0">
                <p>
                  <strong>{item.source_name}</strong> →{" "}
                  <Link href={`/instituciones/${item.institution_id}`} className={linkClass}>
                    {item.institution_name}
                  </Link>
                </p>
                <p className="text-sm">Motivo: {item.note}</p>
                <p className="text-sm text-ink-muted">
                  {item.created_by_email ?? "Cuenta eliminada"} · {formatTimestamp(item.created_at)}
                </p>
                <DeleteMappingForm id={item.id} kind={item.kind} label={`Eliminar el vínculo de ${item.source_name}`} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="titulo-pendientes" className="flex flex-col gap-3">
        <h2 id="titulo-pendientes" className="text-xl font-semibold" role="status">
          {pending.ok ? `Pendientes: ${formatNumber(pending.data.total)}` : "Pendientes"}
        </h2>
        <FilterForm action={BASE_PATH} legend="Buscar pendientes" hasFilters={Boolean(q)}>
          <input type="hidden" name="tipo" value={kind} />
          <TextFilter name="q" label="Nombre en la fuente" value={q} />
        </FilterForm>
        {!pending.ok ? (
          <Notice>{pending.reason}</Notice>
        ) : pending.data.items.length === 0 ? (
          <p className="text-sm">No hay entidades pendientes{q ? " con esa búsqueda" : ""}.</p>
        ) : (
          <ul className="rounded border border-rule bg-surface px-5">
            {pending.data.items.map((item) => (
              <li key={item.source_value} className="border-t border-rule py-4 first:border-t-0">
                <p className="font-medium">{item.source_name}</p>
                <p className="text-sm text-ink-muted">
                  {[item.detail, `${formatNumber(item.records)} ${KINDS[kind].records}`]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
                <p className="text-sm">{item.reason}</p>
                <p className="mt-1 text-sm">
                  <Link href={newHref(item)} className={linkClass}>
                    Vincular {item.source_name}
                  </Link>
                </p>
              </li>
            ))}
          </ul>
        )}
        {pending.ok ? (
          <Pagination
            basePath={BASE_PATH}
            query={{ tipo: kind, q }}
            page={page}
            pageSize={PAGE_SIZE}
            total={pending.data.total}
          />
        ) : null}
      </section>
    </div>
  );
}

export default function VinculosPage(props: PageProps<"/panel/vinculos">) {
  return (
    <Suspense fallback={<p role="status">Cargando…</p>}>
      <Links searchParams={props.searchParams} />
    </Suspense>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { FilterForm, TextFilter } from "@/components/Filters";
import { Notice } from "@/components/Notice";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { MappingForm } from "@/components/StaffForms";
import { fetchInstitutions } from "@/lib/api";
import { param, type SearchParams } from "@/lib/format";
import { requireStaff } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Nuevo vínculo",
  robots: { index: false, follow: false },
};

const BASE_PATH = "/panel/vinculos/nuevo";

/** A first search: the name without a suffix such as " - GESTIÓN GENERAL" or " - ADR". */
function suggestedSearch(name: string): string {
  return name.split(" - ")[0].replace(/[*+]+$/, "").trim();
}

async function NewLink({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const { user, allowed } = await requireStaff(["data_steward"]);
  if (!allowed) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Nuevo vínculo" />
        <Forbidden />
      </div>
    );
  }
  const query = await searchParams;
  const kind = param(query, "tipo") === "contract_entity" ? "contract_entity" : "budget_entity";
  const value = param(query, "valor") ?? "";
  const name = param(query, "nombre") ?? "";
  const q = param(query, "q") ?? suggestedSearch(name);
  const results = q ? await fetchInstitutions({ q, limit: 10 }) : null;
  const back = `/panel/vinculos?tipo=${kind}`;

  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Nuevo vínculo" />
      <p>
        <Link href={back} className="text-brand underline underline-offset-4">
          Volver a los vínculos
        </Link>
      </p>
      {!value ? (
        <Notice>Falta la entidad de la fuente. Elíjala en la lista de pendientes.</Notice>
      ) : (
        <>
          <p>
            Entidad en la fuente ({kind === "budget_entity" ? "presupuesto" : "SECOP II"}):{" "}
            <strong>{name}</strong>
          </p>
          <FilterForm action={BASE_PATH} legend="Buscar en el directorio" hasFilters={false}>
            <input type="hidden" name="tipo" value={kind} />
            <input type="hidden" name="valor" value={value} />
            <input type="hidden" name="nombre" value={name} />
            <TextFilter name="q" label="Nombre en el directorio" value={q} />
          </FilterForm>
          {results === null ? null : !results.ok ? (
            <Notice>{results.reason}</Notice>
          ) : results.data.items.length === 0 ? (
            <Notice>Ninguna entidad del directorio coincide. Pruebe con menos palabras.</Notice>
          ) : (
            <MappingForm
              kind={kind}
              sourceValue={value}
              options={results.data.items.map((item) => ({
                id: item.id,
                name: item.name,
                detail: [item.legal_nature, item.order, item.department].filter(Boolean).join(" · ") || null,
              }))}
            />
          )}
        </>
      )}
    </div>
  );
}

export default function NuevoVinculoPage(props: PageProps<"/panel/vinculos/nuevo">) {
  return (
    <Suspense fallback={<p role="status">Cargando…</p>}>
      <NewLink searchParams={props.searchParams} />
    </Suspense>
  );
}

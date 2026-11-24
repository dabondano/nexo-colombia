import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { FilterForm, SelectFilter, TextFilter } from "@/components/Filters";
import { Notice } from "@/components/Notice";
import { Pagination } from "@/components/Pagination";
import {
  fetchContractFilters,
  fetchContracts,
  fetchInstitution,
  type ContractSummary,
} from "@/lib/api";
import {
  formatCalendarDate,
  formatNumber,
  formatPesos,
  pageNumber,
  param,
  type SearchParams,
} from "@/lib/format";

export const metadata: Metadata = {
  title: "Contratos",
  description:
    "Contratos recientes de las entidades públicas del orden nacional, tomados de SECOP II, con la fuente de cada registro.",
};

const PAGE_SIZE = 25;
const BASE_PATH = "/contratos";
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function ContractItem({ item }: { item: ContractSummary }) {
  const supplier = item.supplier_name ?? item.supplier_label;
  const details = [item.contract_type, item.modality, item.status].filter(Boolean);
  return (
    <li className="border-t border-rule py-4 first:border-t-0">
      <p className="text-sm text-ink-muted">
        Firmado el {formatCalendarDate(item.signed_on)} · {item.entity_name}
      </p>
      <h3 className="mt-1 font-semibold">
        <Link
          href={`${BASE_PATH}/${item.id}`}
          className="line-clamp-3 text-brand underline underline-offset-4"
        >
          {item.purpose}
        </Link>
      </h3>
      <p className="mt-1 text-sm">
        {formatPesos(item.value)} · Contratista: {supplier}
      </p>
      {details.length > 0 ? (
        <p className="mt-1 text-sm text-ink-muted">{details.join(" · ")}</p>
      ) : null}
    </li>
  );
}

async function Listing({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const query = await searchParams;
  const rawEntity = param(query, "entidad");
  const entity = rawEntity && UUID.test(rawEntity) ? rawEntity : undefined;
  const filters = {
    q: param(query, "q"),
    tipo: param(query, "tipo"),
    modalidad: param(query, "modalidad"),
    estado: param(query, "estado"),
    entidad: entity,
  };
  const page = pageNumber(query);
  const hasFilters = Object.values(filters).some(Boolean);

  const [options, result, institution] = await Promise.all([
    fetchContractFilters(),
    fetchContracts({
      q: filters.q,
      institution: entity,
      contract_type: filters.tipo,
      modality: filters.modalidad,
      status: filters.estado,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    }),
    entity ? fetchInstitution(entity) : Promise.resolve(null),
  ]);

  if (!result.ok || !options.ok) {
    const reason = !result.ok ? result.reason : !options.ok ? options.reason : "";
    return <Notice>{reason} Los contratos no están disponibles en este momento.</Notice>;
  }

  const { total, items, window_note } = result.data;
  const first = (page - 1) * PAGE_SIZE + 1;
  const entityName = institution && institution.ok ? institution.data.name : null;

  return (
    <div className="flex flex-col gap-6">
      <p className="max-w-3xl text-sm text-ink-muted">{window_note}</p>
      {entity ? (
        <p className="text-sm">
          Entidad: <strong>{entityName ?? "entidad del directorio"}</strong>{" "}
          <span className="text-ink-muted">(enlazada por NIT)</span> ·{" "}
          <Link href={BASE_PATH} className="text-brand underline underline-offset-4">
            Ver los contratos de todas las entidades
          </Link>
        </p>
      ) : null}
      <FilterForm action={BASE_PATH} legend="Buscar contratos" hasFilters={hasFilters}>
        {entity ? <input type="hidden" name="entidad" value={entity} /> : null}
        <TextFilter
          name="q"
          label="Palabras del objeto del contrato"
          value={filters.q}
          placeholder="Por ejemplo: aseo, vigilancia, interventoría"
        />
        <SelectFilter
          name="tipo"
          label="Tipo de contrato"
          value={filters.tipo}
          options={options.data.contract_type}
        />
        <SelectFilter
          name="modalidad"
          label="Modalidad de contratación"
          value={filters.modalidad}
          options={options.data.modality}
        />
        <SelectFilter name="estado" label="Estado" value={filters.estado} options={options.data.status} />
      </FilterForm>

      <section aria-labelledby="titulo-resultados" className="flex flex-col gap-4">
        <h2 id="titulo-resultados" className="text-xl font-semibold" role="status">
          {total === 0
            ? "Sin resultados"
            : `${formatNumber(total)} ${total === 1 ? "contrato" : "contratos"}`}
          {total > PAGE_SIZE && items.length > 0 ? (
            <span className="text-base font-normal text-ink-muted">
              {" "}
              (se muestran del {formatNumber(first)} al {formatNumber(first + items.length - 1)},
              del más reciente al más antiguo)
            </span>
          ) : null}
        </h2>
        {total === 0 ? (
          <Notice>
            {hasFilters
              ? "Ningún contrato coincide con esta búsqueda. Puede probar con menos palabras o quitar filtros."
              : "Todavía no se han cargado contratos en la plataforma."}
          </Notice>
        ) : items.length === 0 ? (
          <Notice>Esta página de resultados no existe.</Notice>
        ) : (
          <ul className="rounded border border-rule bg-surface px-5">
            {items.map((item) => (
              <ContractItem key={item.id} item={item} />
            ))}
          </ul>
        )}
        <Pagination basePath={BASE_PATH} query={filters} page={page} pageSize={PAGE_SIZE} total={total} />
      </section>
    </div>
  );
}

export default function ContratosPage(props: PageProps<"/contratos">) {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="font-serif text-3xl font-semibold text-brand">Contratos</h1>
      <p className="max-w-3xl text-ink-muted">
        Contratos de las entidades públicas del orden nacional, tomados de SECOP II, la
        plataforma de Colombia Compra Eficiente. Se listan por fecha de firma, sin ordenar ni
        comparar por valor. Las entidades son responsables de lo que publican; cada contrato
        enlaza a su proceso en SECOP.
      </p>
      <Suspense fallback={<p role="status">Cargando los contratos…</p>}>
        <Listing searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

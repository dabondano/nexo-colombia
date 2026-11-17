import Link from "next/link";
import { Suspense } from "react";
import { Notice } from "@/components/Notice";
import { StageBadge } from "@/components/StageBadge";
import { fetchInitiatives, fetchInstitutions, fetchSources, type Source } from "@/lib/api";
import { formatDateTime, formatNumber } from "@/lib/format";
import { MODULES } from "@/lib/modules";

const linkClass = "font-medium text-brand underline underline-offset-4";

type Dataset = {
  sourceRef: string;
  total: number;
  noun: string;
  href: string;
  linkLabel: string;
};

function DatasetCard({ dataset, source }: { dataset: Dataset; source: Source | undefined }) {
  return (
    <li className="rounded border border-rule bg-surface p-5">
      <p className="font-serif text-3xl font-semibold text-brand">
        {formatNumber(dataset.total)}
      </p>
      <p className="text-lg">{dataset.noun}</p>
      {source ? (
        <p className="mt-2 text-sm text-ink-muted">
          Fuente:{" "}
          <a href={source.url} className="underline underline-offset-4" rel="noopener noreferrer">
            {source.name}
          </a>
          , {source.institution}.{" "}
          {source.last_successful_sync
            ? `Obtenido el ${formatDateTime(source.last_successful_sync.finished_at)}.`
            : null}
        </p>
      ) : null}
      <p className="mt-3">
        <Link href={dataset.href} className={linkClass}>
          {dataset.linkLabel}
        </Link>
      </p>
    </li>
  );
}

/** Only counts of records that are really loaded, each with its source. */
async function AvailableData() {
  const [institutions, initiatives, sources] = await Promise.all([
    fetchInstitutions({ limit: 1 }),
    fetchInitiatives({ limit: 1 }),
    fetchSources(),
  ]);

  if (!institutions.ok || !initiatives.ok) {
    return (
      <Notice>
        No fue posible consultar los datos en este momento, por lo que esta página no muestra
        cifras.
      </Notice>
    );
  }

  const datasets: Dataset[] = [
    {
      sourceRef: "datos.gov.co:kcxp-nxum",
      total: initiatives.data.total,
      noun: "proyectos de ley y de acto legislativo",
      href: "/legislacion",
      linkLabel: "Explorar los proyectos de ley",
    },
    {
      sourceRef: "datos.gov.co:h7zv-k39x",
      total: institutions.data.total,
      noun: "entidades públicas",
      href: "/instituciones",
      linkLabel: "Explorar el directorio de instituciones",
    },
  ].filter((dataset) => dataset.total > 0);

  if (datasets.length === 0) {
    return (
      <Notice>
        Todavía no hay datos cargados, por lo que esta página no muestra cifras ni resultados.
      </Notice>
    );
  }

  const byRef = new Map((sources.ok ? sources.data : []).map((s) => [s.external_ref, s]));
  return (
    <ul className="grid gap-4 sm:grid-cols-2">
      {datasets.map((dataset) => (
        <DatasetCard key={dataset.sourceRef} dataset={dataset} source={byRef.get(dataset.sourceRef)} />
      ))}
    </ul>
  );
}

export default function HomePage() {
  return (
    <div className="flex flex-col gap-12">
      <section aria-labelledby="titulo-inicio" className="flex flex-col gap-4">
        <h1 id="titulo-inicio" className="font-serif text-4xl font-semibold text-brand">
          Comprende el Estado. Explora sus instituciones. Investiga sus decisiones.
        </h1>
        <p className="max-w-3xl text-lg text-ink-muted">
          NEXO Colombia reunirá en un solo lugar la información pública sobre el Estado
          colombiano: sus normas, sus instituciones, sus servidores, sus recursos y sus
          decisiones. Cada dato muestra su fuente para que cualquier persona pueda
          verificarlo.
        </p>
      </section>

      <section aria-labelledby="titulo-datos" className="flex flex-col gap-4">
        <h2 id="titulo-datos" className="text-xl font-semibold">
          Datos disponibles hoy
        </h2>
        <Suspense fallback={<p role="status">Consultando los datos disponibles…</p>}>
          <AvailableData />
        </Suspense>
        <p className="max-w-3xl text-sm text-ink-muted">
          La plataforma está en construcción. Estas cifras cuentan únicamente los registros ya
          cargados desde fuentes oficiales; no representan la totalidad de la información
          pública.{" "}
          <Link href="/fuentes" className="underline underline-offset-4">
            Consultar el registro de fuentes
          </Link>
          .
        </p>
      </section>

      <section aria-labelledby="titulo-modulos" className="flex flex-col gap-4">
        <h2 id="titulo-modulos" className="text-xl font-semibold">
          Módulos previstos
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2">
          {MODULES.map((module) => (
            <li key={module.number} className="rounded border border-rule bg-surface p-5">
              <div className="flex items-start justify-between gap-4">
                <h3 className="text-lg font-semibold">
                  <span className="mr-2 font-serif text-accent">{module.number}</span>
                  {module.name}
                </h3>
                <StageBadge stage={module.stage} />
              </div>
              <p className="mt-2 text-ink-muted">{module.summary}</p>
              {module.available ? (
                <p className="mt-3">
                  <span className="text-ink-muted">Primera parte disponible: </span>
                  <Link href={module.available.href} className={linkClass}>
                    {module.available.label}
                  </Link>
                </p>
              ) : null}
            </li>
          ))}
        </ul>
        <p className="text-sm text-ink-muted">
          Etapas de avance: Diseñado, Implementado, Probado, Integrado y Desplegado. La etapa
          describe el módulo completo y solo cambia cuando existe evidencia de ello.
        </p>
      </section>
    </div>
  );
}

import type { Metadata } from "next";
import { Suspense } from "react";
import { ScrollRegion } from "@/components/ScrollRegion";
import { fetchSources, type Source } from "@/lib/api";

export const metadata: Metadata = {
  title: "Fuentes",
  description: "Registro de las fuentes de información que utiliza NEXO Colombia.",
};

const dateFormat = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "long",
  timeZone: "America/Bogota",
});

function formatDate(value: string | null): string {
  return value ? dateFormat.format(new Date(value)) : "Sin registro";
}

function SourceRow({ source }: { source: Source }) {
  const verified = source.verification_status === "verified";
  return (
    <tr className="border-t border-rule align-top">
      <th scope="row" className="py-3 pr-4 text-left font-medium">
        <a
          href={source.url}
          className="text-brand underline underline-offset-4"
          rel="noopener noreferrer"
        >
          {source.name}
        </a>
        <div className="font-normal text-ink-muted">{source.institution}</div>
      </th>
      <td className="py-3 pr-4">{source.licence ?? "No indicada"}</td>
      <td className="py-3 pr-4">
        <span className={verified ? "text-ok" : "text-warn"}>
          {verified ? "Verificada" : "Sin verificar"}
        </span>
        <div className="text-ink-muted">{formatDate(source.last_verified_at)}</div>
      </td>
      <td className="py-3">
        {source.last_successful_sync
          ? `${formatDate(source.last_successful_sync.finished_at)} · ${source.last_successful_sync.rows_seen.toLocaleString("es-CO")} registros`
          : "Aún no se ha sincronizado"}
      </td>
    </tr>
  );
}

async function SourceList() {
  const result = await fetchSources();

  if (!result.ok) {
    return (
      <p role="status" className="rounded border border-rule bg-surface p-5">
        {result.reason} El registro de fuentes no está disponible en este momento.
      </p>
    );
  }

  if (result.data.length === 0) {
    return (
      <p role="status" className="rounded border border-rule bg-surface p-5">
        Todavía no hay fuentes registradas en la plataforma. Las fuentes aparecerán aquí
        cuando se conecten y se verifiquen.
      </p>
    );
  }

  return (
    <ScrollRegion label="Tabla de fuentes" className="rounded border border-rule bg-surface p-5">
      <table className="w-full text-sm">
        <caption className="sr-only">Fuentes de información registradas</caption>
        <thead>
          <tr className="text-left text-ink-muted">
            <th scope="col" className="pb-2 pr-4 font-medium">Fuente</th>
            <th scope="col" className="pb-2 pr-4 font-medium">Licencia</th>
            <th scope="col" className="pb-2 pr-4 font-medium">Verificación</th>
            <th scope="col" className="pb-2 font-medium">Última sincronización</th>
          </tr>
        </thead>
        <tbody>
          {result.data.map((source) => (
            <SourceRow key={source.id} source={source} />
          ))}
        </tbody>
      </table>
    </ScrollRegion>
  );
}

export default function FuentesPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="font-serif text-3xl font-semibold text-brand">Fuentes</h1>
      <p className="max-w-3xl text-ink-muted">
        NEXO Colombia solo publica información que puede rastrearse hasta su origen. Este
        registro muestra cada fuente, su licencia, si ha sido verificada y cuándo se
        sincronizó por última vez.
      </p>
      <Suspense fallback={<p role="status">Cargando el registro de fuentes…</p>}>
        <SourceList />
      </Suspense>
    </div>
  );
}

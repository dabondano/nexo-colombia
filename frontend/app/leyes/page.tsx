import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Notice } from "@/components/Notice";
import { fetchInstruments, lawName } from "@/lib/api";
import { formatCalendarDate } from "@/lib/format";

export const metadata: Metadata = {
  title: "Leyes",
  description:
    "Leyes clave sobre transparencia, contratación pública, participación y el Congreso, artículo por artículo y con su fuente.",
};

const linkClass = "text-brand underline underline-offset-4";

async function Laws() {
  const result = await fetchInstruments();
  if (!result.ok) {
    return <Notice>{result.reason} Las leyes no están disponibles en este momento.</Notice>;
  }
  const laws = result.data.filter((item) => item.instrument_type.startsWith("ley"));
  if (laws.length === 0) {
    return <Notice>Todavía no se han cargado leyes en NEXO.</Notice>;
  }
  return (
    <ul className="flex flex-col gap-3">
      {laws.map((law) => (
        <li key={law.id} className="rounded border border-rule bg-surface p-5">
          <h2 className="text-lg font-semibold">
            <Link href={`/leyes/${law.slug}`} className={linkClass}>
              {lawName(law)}
            </Link>
          </h2>
          <p className="mt-1">{law.title.replace(`${lawName(law)}, `, "")}</p>
          {law.promulgated_on ? (
            <p className="mt-1 text-sm text-ink-muted">
              Expedida el {formatCalendarDate(law.promulgated_on)}
            </p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export default function LeyesPage() {
  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-3">
        <h1 className="font-serif text-3xl font-semibold text-brand">Leyes</h1>
        <p className="max-w-3xl text-lg text-ink-muted">
          Una selección de leyes clave sobre transparencia, contratación pública, participación
          ciudadana, administración pública y el Congreso, artículo por artículo, tal como las
          publica Función Pública en su Gestor Normativo. Es una edición informativa: el texto con
          valor oficial es el del Diario Oficial.
        </p>
        <p className="text-sm">
          La{" "}
          <Link href="/constitucion" className={linkClass}>
            Constitución Política
          </Link>{" "}
          tiene su propia sección.
        </p>
      </header>
      <Suspense fallback={<p role="status">Cargando las leyes…</p>}>
        <Laws />
      </Suspense>
    </div>
  );
}

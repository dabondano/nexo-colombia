import Link from "next/link";
import { StageBadge } from "@/components/StageBadge";
import { MODULES } from "@/lib/modules";

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
          decisiones. Cada dato mostrará su fuente para que cualquier persona pueda
          verificarlo.
        </p>
      </section>

      <section
        aria-labelledby="titulo-estado"
        className="rounded border border-rule bg-surface p-6"
      >
        <h2 id="titulo-estado" className="text-xl font-semibold">
          Estado del proyecto
        </h2>
        <p className="mt-2 max-w-3xl text-ink-muted">
          La plataforma está en construcción. Todavía no hay datos cargados, por lo que esta
          página no muestra cifras, actividad reciente ni resultados de búsqueda. Los
          módulos aparecerán aquí a medida que funcionen con datos reales y verificables.
        </p>
        <p className="mt-4">
          <Link href="/fuentes" className="font-medium text-brand underline underline-offset-4">
            Consultar el registro de fuentes
          </Link>
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
            </li>
          ))}
        </ul>
        <p className="text-sm text-ink-muted">
          Etapas de avance: Diseñado, Implementado, Probado, Integrado y Desplegado. Un módulo
          solo cambia de etapa cuando existe evidencia de ello.
        </p>
      </section>
    </div>
  );
}

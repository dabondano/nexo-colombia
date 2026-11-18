import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { PanelHeader } from "@/components/PanelHeader";
import { requireStaff } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Panel del equipo",
  robots: { index: false, follow: false },
};

const linkClass = "text-brand underline underline-offset-4";

async function Overview() {
  const { user } = await requireStaff();
  const steward = user.role === "admin" || user.role === "data_steward";
  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Panel del equipo" />
      <ul className="flex flex-col gap-4">
        {steward ? (
          <li className="rounded border border-rule bg-surface p-5">
            <h2 className="text-xl font-semibold">
              <Link href="/panel/sincronizaciones" className={linkClass}>
                Sincronizaciones
              </Link>
            </h2>
            <p className="mt-1 text-sm text-ink-muted">
              Cada carga de datos con sus cifras y las filas rechazadas con su motivo.
            </p>
          </li>
        ) : null}
        {user.role === "admin" ? (
          <>
            <li className="rounded border border-rule bg-surface p-5">
              <h2 className="text-xl font-semibold">
                <Link href="/panel/usuarios" className={linkClass}>
                  Cuentas
                </Link>
              </h2>
              <p className="mt-1 text-sm text-ink-muted">
                Crear cuentas, cambiar roles, desactivar y restablecer contraseñas.
              </p>
            </li>
            <li className="rounded border border-rule bg-surface p-5">
              <h2 className="text-xl font-semibold">
                <Link href="/panel/auditoria" className={linkClass}>
                  Registro de auditoría
                </Link>
              </h2>
              <p className="mt-1 text-sm text-ink-muted">
                Ingresos, cambios de cuentas y sincronizaciones. No se puede modificar ni borrar.
              </p>
            </li>
          </>
        ) : null}
        {user.role === "legal_reviewer" || user.role === "admin" ? (
          <li className="rounded border border-rule bg-surface p-5">
            <h2 className="text-xl font-semibold">
              <Link href="/panel/revision" className={linkClass}>
                Revisión jurídica
              </Link>
            </h2>
            <p className="mt-1 text-sm text-ink-muted">
              Revisar las lecciones y los artículos de la Constitución que requieren revisión. Una
              aprobación vale solo para el contenido exacto revisado.
            </p>
          </li>
        ) : null}
      </ul>
    </div>
  );
}

export default function PanelPage() {
  return (
    <Suspense fallback={<p role="status">Cargando el panel…</p>}>
      <Overview />
    </Suspense>
  );
}

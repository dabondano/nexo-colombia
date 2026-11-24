import Link from "next/link";
import { signOut } from "@/app/panel/actions";
import { ROLE_LABELS, type StaffUser } from "@/lib/staff";

const linkClass = "text-brand underline underline-offset-4";

/** Who is signed in, the panel sections their role can use, and sign-out. */
export function PanelHeader({ user, title }: { user: StaffUser; title: string }) {
  const steward = user.role === "admin" || user.role === "data_steward";
  const admin = user.role === "admin";
  const reviewer = admin || user.role === "legal_reviewer";
  return (
    <header className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded border border-rule bg-surface p-4 text-sm">
        <p>
          <span className="font-medium">{user.display_name}</span> · {user.email} ·{" "}
          {ROLE_LABELS[user.role]}
        </p>
        <form action={signOut}>
          <button type="submit" className="rounded border border-rule px-4 py-1.5 text-brand hover:underline">
            Cerrar sesión
          </button>
        </form>
      </div>
      {user.must_change_password ? null : (
        <nav aria-label="Secciones del panel">
          <ul className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <li>
              <Link href="/panel" className={linkClass}>
                Inicio del panel
              </Link>
            </li>
            {steward ? (
              <li>
                <Link href="/panel/sincronizaciones" className={linkClass}>
                  Sincronizaciones
                </Link>
              </li>
            ) : null}
            {steward ? (
              <li>
                <Link href="/panel/calidad" className={linkClass}>
                  Calidad de los datos
                </Link>
              </li>
            ) : null}
            {reviewer ? (
              <li>
                <Link href="/panel/revision" className={linkClass}>
                  Revisión jurídica
                </Link>
              </li>
            ) : null}
            {admin ? (
              <>
                <li>
                  <Link href="/panel/usuarios" className={linkClass}>
                    Cuentas
                  </Link>
                </li>
                <li>
                  <Link href="/panel/auditoria" className={linkClass}>
                    Registro de auditoría
                  </Link>
                </li>
              </>
            ) : null}
            <li>
              <Link href="/panel/contrasena" className={linkClass}>
                Cambiar contraseña
              </Link>
            </li>
          </ul>
        </nav>
      )}
      <h1 className="font-serif text-3xl font-semibold text-brand">{title}</h1>
    </header>
  );
}

export function Forbidden() {
  return (
    <p role="status" className="rounded border border-rule bg-surface p-5">
      Su rol no permite ver esta sección.
    </p>
  );
}

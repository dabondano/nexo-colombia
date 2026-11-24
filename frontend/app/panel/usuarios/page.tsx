import type { Metadata } from "next";
import { Suspense } from "react";
import { Forbidden, PanelHeader } from "@/components/PanelHeader";
import { Notice } from "@/components/Notice";
import { CreateUserForm, UserControls } from "@/components/StaffForms";
import { ROLE_LABELS, formatTimestamp, requireStaff, staffRequest, type StaffUser } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Cuentas del equipo",
  robots: { index: false, follow: false },
};

async function Users() {
  const { user, allowed } = await requireStaff(["admin"]);
  if (!allowed) {
    return (
      <div className="flex flex-col gap-6">
        <PanelHeader user={user} title="Cuentas del equipo" />
        <Forbidden />
      </div>
    );
  }
  const result = await staffRequest<StaffUser[]>("/admin/users");
  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Cuentas del equipo" />
      <section aria-labelledby="titulo-nueva" className="flex flex-col gap-3">
        <h2 id="titulo-nueva" className="text-xl font-semibold">
          Nueva cuenta
        </h2>
        <CreateUserForm />
      </section>
      <section aria-labelledby="titulo-cuentas" className="flex flex-col gap-3">
        <h2 id="titulo-cuentas" className="text-xl font-semibold">
          Cuentas existentes
        </h2>
        {!result.ok ? (
          <Notice>{result.reason}</Notice>
        ) : (
          <ul className="flex flex-col gap-4">
            {result.data.map((account) => (
              <li key={account.id} className="rounded border border-rule bg-surface p-5">
                <h3 className="text-lg font-semibold">{account.display_name}</h3>
                <p className="text-sm text-ink-muted">
                  {account.email} · {ROLE_LABELS[account.role]} ·{" "}
                  {account.is_active ? "Activa" : "Desactivada"}
                  {account.must_change_password ? " · Debe cambiar la contraseña" : ""} · Último
                  ingreso: {formatTimestamp(account.last_login_at)}
                </p>
                {account.id === user.id ? (
                  <p className="mt-2 text-sm text-ink-muted">Esta es su cuenta.</p>
                ) : (
                  <div className="mt-3">
                    <UserControls
                      id={account.id}
                      email={account.email}
                      role={account.role}
                      isActive={account.is_active}
                    />
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

export default function UsuariosPage() {
  return (
    <Suspense fallback={<p role="status">Cargando las cuentas…</p>}>
      <Users />
    </Suspense>
  );
}

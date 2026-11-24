import type { Metadata } from "next";
import { Suspense } from "react";
import { PanelHeader } from "@/components/PanelHeader";
import { PasswordForm } from "@/components/StaffForms";
import { requireStaff } from "@/lib/staff";

export const metadata: Metadata = {
  title: "Cambiar contraseña",
  robots: { index: false, follow: false },
};

async function PasswordSection() {
  const { user } = await requireStaff([], { allowPasswordChange: true });
  return (
    <div className="flex flex-col gap-6">
      <PanelHeader user={user} title="Cambiar contraseña" />
      {user.must_change_password ? (
        <p role="status" className="rounded border border-rule bg-surface p-5">
          Su contraseña fue asignada por la administración. Elija una propia para continuar.
        </p>
      ) : null}
      <p className="max-w-3xl text-sm text-ink-muted">
        Use al menos 12 caracteres; una frase de varias palabras es fácil de recordar y difícil de
        adivinar. Al cambiarla se cierran sus otras sesiones abiertas.
      </p>
      <PasswordForm />
    </div>
  );
}

export default function ContrasenaPage() {
  return (
    <Suspense fallback={<p role="status">Cargando…</p>}>
      <PasswordSection />
    </Suspense>
  );
}

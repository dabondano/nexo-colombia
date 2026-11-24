import type { Metadata } from "next";
import { LoginForm } from "@/components/StaffForms";

export const metadata: Metadata = {
  title: "Acceso del equipo",
  robots: { index: false, follow: false },
};

export default function IngresarPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="font-serif text-3xl font-semibold text-brand">Acceso del equipo</h1>
      <p className="max-w-3xl text-ink-muted">
        Solo para el equipo de NEXO Colombia (administración, gestión de datos y revisión
        jurídica). El sitio público no requiere cuenta. Las cuentas las crea la administración.
      </p>
      <LoginForm />
    </div>
  );
}

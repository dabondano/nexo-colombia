import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-serif text-3xl font-semibold text-brand">Página no encontrada</h1>
      <p className="max-w-3xl text-ink-muted">
        Esta dirección no corresponde a ninguna página ni a ningún registro de NEXO Colombia.
      </p>
      <p>
        <Link href="/" className="font-medium text-brand underline underline-offset-4">
          Volver al inicio
        </Link>
      </p>
    </div>
  );
}

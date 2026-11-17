import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "NEXO Colombia",
    template: "%s · NEXO Colombia",
  },
  description:
    "Sistema de Conocimiento e Inteligencia Pública. Comprende el Estado. Explora sus instituciones. Investiga sus decisiones.",
};

const NAV = [
  { href: "/", label: "Inicio" },
  { href: "/legislacion", label: "Legislación" },
  { href: "/instituciones", label: "Instituciones" },
  { href: "/fuentes", label: "Fuentes" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es-CO" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded focus:bg-surface focus:px-4 focus:py-2 focus:text-ink"
        >
          Saltar al contenido
        </a>
        <header className="border-b border-rule bg-brand text-brand-ink">
          <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-x-8 gap-y-2 px-4 py-4">
            <Link href="/" className="flex flex-col leading-tight">
              <span className="font-serif text-2xl font-semibold tracking-wide">NEXO Colombia</span>
              <span className="text-sm opacity-90">
                Sistema de Conocimiento e Inteligencia Pública
              </span>
            </Link>
            <div className="flex flex-col gap-3 sm:items-end">
              <form
                action="/buscar"
                method="get"
                role="search"
                aria-label="Búsqueda en todo el sitio"
                className="flex gap-2"
              >
                <label htmlFor="busqueda-global" className="sr-only">
                  Buscar en NEXO Colombia
                </label>
                <input
                  id="busqueda-global"
                  name="q"
                  type="search"
                  required
                  maxLength={200}
                  placeholder="Buscar proyectos y entidades"
                  className="w-full min-w-0 rounded border border-brand-ink/40 bg-surface px-3 py-1.5 text-base text-ink sm:w-72"
                />
                <button
                  type="submit"
                  className="rounded border border-brand-ink/60 px-4 py-1.5 font-medium hover:bg-brand-ink/10"
                >
                  Buscar
                </button>
              </form>
              <nav aria-label="Navegación principal">
                <ul className="flex flex-wrap gap-x-6 gap-y-1 text-base">
                  {NAV.map((item) => (
                    <li key={item.href}>
                      <Link href={item.href} className="underline-offset-4 hover:underline">
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </div>
        </header>
        <main id="contenido" className="mx-auto w-full max-w-5xl flex-1 px-4 py-10">
          {children}
        </main>
        <footer className="border-t border-rule">
          <div className="mx-auto w-full max-w-5xl px-4 py-6 text-sm text-ink-muted">
            <p>
              NEXO Colombia es un proyecto de interés público en construcción. No representa a
              ninguna entidad del Estado ni a ningún partido o movimiento político.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

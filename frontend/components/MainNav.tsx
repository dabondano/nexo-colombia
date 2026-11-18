"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Inicio" },
  { href: "/aprender", label: "Aprender" },
  { href: "/constitucion", label: "Constitución" },
  { href: "/legislacion", label: "Legislación" },
  { href: "/representantes", label: "Representantes" },
  { href: "/instituciones", label: "Instituciones" },
  { href: "/fuentes", label: "Fuentes" },
];

function isCurrent(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

/** The links; `pathname` null renders them without marking a current section. */
export function NavLinks({ pathname }: { pathname: string | null }) {
  return (
    <nav aria-label="Navegación principal">
      <ul className="flex flex-wrap gap-x-6 gap-y-1 text-base">
        {NAV.map((item) => {
          const current = pathname !== null && isCurrent(pathname, item.href);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={current ? "page" : undefined}
                className={
                  current
                    ? "font-semibold underline decoration-2 underline-offset-4"
                    : "underline-offset-4 hover:underline"
                }
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/**
 * Main navigation; the current section is announced and underlined. Reading the
 * address must happen inside <Suspense> with Cache Components, so the layout wraps
 * this in one whose fallback is <NavLinks pathname={null} />.
 */
export function MainNav() {
  return <NavLinks pathname={usePathname()} />;
}

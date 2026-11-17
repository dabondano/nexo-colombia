import Link from "next/link";
import { formatNumber } from "@/lib/format";

type Props = {
  basePath: string;
  /** Current filters, without the page number. */
  query: Record<string, string | undefined>;
  page: number;
  pageSize: number;
  total: number;
};

function href(basePath: string, query: Props["query"], page: number): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value) params.set(key, value);
  }
  if (page > 1) params.set("pagina", String(page));
  const text = params.toString();
  return text ? `${basePath}?${text}` : basePath;
}

export function Pagination({ basePath, query, page, pageSize, total }: Props) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages === 1) return null;
  const linkClass = "rounded border border-rule bg-surface px-4 py-2 text-brand hover:underline";
  return (
    <nav aria-label="Páginas de resultados" className="flex flex-wrap items-center gap-4">
      {page > 1 ? (
        <Link href={href(basePath, query, page - 1)} className={linkClass} rel="prev">
          Anterior
        </Link>
      ) : null}
      <span className="text-ink-muted">
        Página {formatNumber(page)} de {formatNumber(pages)}
      </span>
      {page < pages ? (
        <Link href={href(basePath, query, page + 1)} className={linkClass} rel="next">
          Siguiente
        </Link>
      ) : null}
    </nav>
  );
}

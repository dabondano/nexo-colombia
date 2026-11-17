import Link from "next/link";
import type { FilterOption } from "@/lib/api";
import { formatNumber } from "@/lib/format";

const fieldClass =
  "w-full rounded border border-rule bg-surface px-3 py-2 text-base text-ink";

export function TextFilter(props: {
  name: string;
  label: string;
  value: string | undefined;
  placeholder?: string;
}) {
  const id = `filtro-${props.name}`;
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium">
        {props.label}
      </label>
      <input
        id={id}
        name={props.name}
        type="search"
        defaultValue={props.value ?? ""}
        placeholder={props.placeholder}
        maxLength={200}
        className={fieldClass}
      />
    </div>
  );
}

export function SelectFilter(props: {
  name: string;
  label: string;
  value: string | undefined;
  options: FilterOption[];
}) {
  const id = `filtro-${props.name}`;
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium">
        {props.label}
      </label>
      <select id={id} name={props.name} defaultValue={props.value ?? ""} className={fieldClass}>
        <option value="">Todos</option>
        {props.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.value} ({formatNumber(option.count)})
          </option>
        ))}
      </select>
    </div>
  );
}

/** A plain GET form: works without JavaScript and keeps the search in the address bar. */
export function FilterForm(props: {
  action: string;
  legend: string;
  hasFilters: boolean;
  children: React.ReactNode;
}) {
  return (
    <form
      action={props.action}
      method="get"
      role="search"
      aria-label={props.legend}
      className="rounded border border-rule bg-surface p-5"
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{props.children}</div>
      <div className="mt-4 flex flex-wrap items-center gap-4">
        <button
          type="submit"
          className="rounded bg-brand px-5 py-2 font-medium text-brand-ink hover:opacity-90"
        >
          Buscar
        </button>
        {props.hasFilters ? (
          <Link href={props.action} className="text-brand underline underline-offset-4">
            Quitar filtros
          </Link>
        ) : null}
      </div>
    </form>
  );
}

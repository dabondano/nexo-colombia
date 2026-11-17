/** A plain status message: empty states and unavailable data, stated honestly. */
export function Notice({ children }: { children: React.ReactNode }) {
  return (
    <p role="status" className="rounded border border-rule bg-surface p-5">
      {children}
    </p>
  );
}

export function Field({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-x-4 gap-y-1 border-t border-rule py-2 sm:grid-cols-[14rem_1fr]">
      <dt className="font-medium">{term}</dt>
      <dd>{children}</dd>
    </div>
  );
}

export const NOT_IN_SOURCE = "No aparece en la fuente";

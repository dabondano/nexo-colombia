/** Marks that the API puts around words the source prints struck through. */
const STRUCK = /⟦([^⟧]*)⟧/g;

export function hasStruckText(text: string): boolean {
  return text.includes("⟦");
}

/** Text as the source prints it, with its struck-through words shown struck through. */
export function SourceText({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(STRUCK)) {
    parts.push(text.slice(last, match.index));
    parts.push(
      <s key={match.index} className="text-ink-muted">
        <span className="sr-only">(tachado en la fuente: </span>
        {match[1]}
        <span className="sr-only">)</span>
      </s>,
    );
    last = match.index + match[0].length;
  }
  parts.push(text.slice(last));
  return <>{parts}</>;
}

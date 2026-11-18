/**
 * A wide table or block that may scroll sideways on small screens. It can take
 * keyboard focus, so people who do not use a mouse can scroll it with the arrow
 * keys (WCAG 2.1.1; axe rule "scrollable-region-focusable").
 */
export function ScrollRegion({
  label,
  className = "",
  children,
}: {
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div role="region" aria-label={label} tabIndex={0} className={`overflow-x-auto ${className}`}>
      {children}
    </div>
  );
}

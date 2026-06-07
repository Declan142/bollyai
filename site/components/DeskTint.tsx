import type { DeskSlug } from "../lib/desks";

export function DeskTint({
  desk,
  children,
  className = ""
}: {
  desk: DeskSlug;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <main data-desk={desk} className={className}>
      {children}
    </main>
  );
}

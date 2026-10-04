import type { ReactNode } from "react";
import Wordmark from "./Wordmark";

/** The system's 80px top bar for pages without replay controls. */
export default function PageHeader({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <header className="sticky top-0 z-40 flex h-20 items-center gap-3 bg-gray-100 px-4 md:px-8 lg:top-[var(--frame)] lg:rounded-tr-2xl">
      <p className="mr-auto flex items-baseline gap-3 text-gray-900">
        <Wordmark className="text-[26px] leading-none sm:text-[30px]" />
        <span className="text-h4 text-gray-700">{title}</span>
      </p>
      {children}
    </header>
  );
}

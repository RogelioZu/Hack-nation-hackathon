"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, GitBranch, Waypoints, type LucideIcon } from "lucide-react";
import Wordmark from "./Wordmark";

// `footer`: on desktop the item leaves the main nav and sits in the footer, above Repository.
const NAV: { href: string; label: string; icon: LucideIcon; match: (p: string) => boolean; footer?: boolean }[] = [
  { href: "/", label: "Discovery", icon: Waypoints, match: (p) => p === "/" },
  { href: "/guide", label: "Reading guide", icon: BookOpen, match: (p) => p.startsWith("/guide"), footer: true },
];

/** Solid blue sidebar: expanded on desktop, icon rail on tablet, bottom bar on phones. */
export default function Sidebar() {
  const pathname = usePathname();
  const guideActive = pathname.startsWith("/guide");
  return (
    <aside
      className="fixed inset-x-0 bottom-0 z-50 flex h-16 items-center bg-blue-500 px-4 text-white md:inset-y-0 md:right-auto md:h-auto md:w-[72px] md:flex-col md:items-stretch md:px-4 md:py-6 lg:top-[var(--frame)] lg:bottom-[var(--frame)] lg:left-[var(--frame)] lg:w-[var(--sidebar)]"
      aria-label="tiemPO"
    >
      <Link
        href="/"
        aria-label="tiemPO, discovery"
        className="mb-8 hidden rounded-sm px-3 pt-2 text-white focus-visible:outline-white lg:block"
      >
        <Wordmark className="text-[30px] leading-none" />
      </Link>

      <nav aria-label="Main" className="flex flex-1 justify-around gap-2 md:flex-none md:flex-col md:justify-start">
        {NAV.map(({ href, label, icon: Icon, match, footer }) => {
          const active = match(pathname);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={`flex h-12 flex-col items-center justify-center gap-0.5 rounded-xl px-3 text-caption font-medium whitespace-nowrap transition-colors duration-[120ms] focus-visible:outline-white md:h-10 md:flex-row md:gap-3 md:rounded-full md:text-body lg:justify-start ${
                active ? "bg-white text-blue-500" : "text-white hover:bg-blue-700"
              } ${footer ? "lg:hidden" : ""}`}
            >
              <Icon aria-hidden size={20} strokeWidth={1.75} />
              <span className="md:sr-only lg:not-sr-only">{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto hidden pb-8 lg:block">
        <div className="flex flex-col gap-2">
          <Link
            href="/guide"
            aria-current={guideActive ? "page" : undefined}
            className={`flex h-10 items-center gap-3 rounded-full px-3 text-body font-medium transition-colors duration-[120ms] focus-visible:outline-white ${
              guideActive ? "bg-white text-blue-500" : "text-white hover:bg-blue-700"
            }`}
          >
            <BookOpen aria-hidden size={20} strokeWidth={1.75} />
            Reading guide
          </Link>
          <a
            href="https://github.com/RogelioZu/Hack-nation-hackathon"
            target="_blank"
            rel="noreferrer"
            className="flex h-10 items-center gap-3 rounded-full px-3 text-body font-medium text-white transition-colors duration-[120ms] hover:bg-blue-700 focus-visible:outline-white"
          >
            <GitBranch aria-hidden size={20} strokeWidth={1.75} />
            Repository
          </a>
        </div>
      </div>
    </aside>
  );
}

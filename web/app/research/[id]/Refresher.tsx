"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** Simple polling: re-render the server component every few seconds while the loop runs. */
export default function Refresher({ intervalMs = 5000 }: { intervalMs?: number }) {
  const router = useRouter();
  useEffect(() => {
    const id = setInterval(() => router.refresh(), intervalMs);
    return () => clearInterval(id);
  }, [router, intervalMs]);
  return null;
}

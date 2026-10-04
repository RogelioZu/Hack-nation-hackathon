import type { Metadata } from "next";
import { Geist_Mono, Inter, Montserrat } from "next/font/google";
import Sidebar from "./_components/Sidebar";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
const montserrat = Montserrat({ variable: "--font-montserrat", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "tiemPO",
  description:
    "An agentic scientific lab on ENUT 2024: agents examine evidence, name the uncertainty, choose the next experiment and update the decision.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${geistMono.variable} ${montserrat.variable}`}>
      <body className="min-h-dvh">
        <div aria-hidden className="app-frame hidden lg:block" />
        <Sidebar />
        <div className="pb-20 md:pb-0 md:pl-[72px] lg:py-3 lg:pr-3 lg:pl-[calc(var(--sidebar)+var(--frame))]">{children}</div>
      {/* impeccable-live-start */}
<script src="http://localhost:8400/live.js?token=a4aa66f0-1159-4391-b7ec-6c29bba3ae3c"></script>
{/* impeccable-live-end */}
</body>
    </html>
  );
}

/** The product name as a wordmark: Montserrat Black, tight tracking, the user's own casing. */
export default function Wordmark({ className = "" }: { className?: string }) {
  return <span className={`font-wordmark font-black tracking-[-0.04em] ${className}`}>tiemPO</span>;
}

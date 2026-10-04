import PageHeader from "../_components/PageHeader";
import SpineGuide from "../_components/discovery/SpineGuide";

export const metadata = { title: "Reading guide · tiemPO" };

export default function GuidePage() {
  return (
    <>
      <PageHeader title="Reading guide" />
      <main className="px-4 pb-12 md:px-8">
        <SpineGuide />
      </main>
    </>
  );
}

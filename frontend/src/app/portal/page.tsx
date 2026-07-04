import { Suspense } from "react"
import ShaderShowcase from "@/components/ui/hero";

export default function PortalPage() {
  return (
    <main className="min-h-screen w-full">
      <Suspense fallback={<p className="p-8 text-center text-white/50">Loading…</p>}>
        <ShaderShowcase />
      </Suspense>
    </main>
  );
}

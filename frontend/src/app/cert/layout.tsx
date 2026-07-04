import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "EVA Certified · VoiceIQ EVA",
  description:
    "100% composite pass@1 on ServiceNow EVA-Bench — 15 enterprise voice scenarios (airline, healthcare HR, ITSM).",
  openGraph: {
    title: "EVA Certified Agent Prompts · VoiceIQ EVA",
    description:
      "Pre-launch QA: 100% pass on 15 EVA-Bench scenarios. Verify live.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "EVA Certified · VoiceIQ EVA",
    description: "100% composite pass@1 on Hugging Face EVA-Bench.",
  },
}

export default function CertLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}

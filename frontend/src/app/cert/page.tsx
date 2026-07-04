"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import benchmark from "@/data/eva-benchmark-results.json"
import type { EvaBenchmarkSummary } from "@/lib/voiceiq-eva"

const CERT_ID = "VIQ-EVA-2026-0703"
const VERIFY_URL = "https://voice-agent-amber-nine.vercel.app/cert"

export default function EvaCertPage() {
  const summary = benchmark.summary as EvaBenchmarkSummary
  const pct = (n: number) => `${(n * 100).toFixed(0)}%`

  const linkedInUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(VERIFY_URL)}`

  return (
    <div className="min-h-screen bg-[#030712] text-white">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900/30 via-transparent to-orange-900/20" />

      <header className="relative z-10 mx-auto flex max-w-4xl items-center justify-between px-6 py-8">
        <Link href="/" className="text-xs uppercase tracking-widest text-white/40 hover:text-white">
          ← VoiceIQ
        </Link>
        <Link
          href="/retell"
          className="text-xs uppercase tracking-widest text-cyan-400 hover:text-cyan-300"
        >
          For Retell →
        </Link>
      </header>

      <main className="relative z-10 mx-auto max-w-4xl px-6 pb-20">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="relative overflow-hidden rounded-3xl border border-cyan-500/30 bg-gradient-to-br from-white/[0.08] to-white/[0.02] p-10 shadow-2xl shadow-cyan-500/10 backdrop-blur-xl"
        >
          <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-emerald-500/20 blur-3xl" />
          <div className="absolute -bottom-8 -left-8 h-32 w-32 rounded-full bg-orange-500/20 blur-3xl" />

          <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-cyan-400">
            VoiceIQ EVA · Pre-Launch Certification
          </p>
          <h1 className="mt-4 text-4xl font-black tracking-tight md:text-5xl">
            EVA Certified
          </h1>
          <p className="mt-2 text-lg text-white/60">
            ServiceNow EVA-Bench · 15 enterprise scenarios · Live verified run
          </p>

          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <Stat label="Composite pass@1" value={pct(summary.composite_pass_at_1)} highlight />
            <Stat label="EVA-A pass@1" value={pct(summary.eva_a_pass_at_1)} />
            <Stat label="EVA-X pass@1" value={pct(summary.eva_x_pass_at_1)} />
          </div>

          <div className="mt-10 space-y-3 border-t border-white/10 pt-8">
            <p className="text-[10px] uppercase tracking-widest text-white/40">Domain breakdown</p>
            {Object.entries(summary.by_domain).map(([domain, stats]) => (
              <div key={domain} className="flex items-center justify-between text-sm">
                <span className="text-white/70">{domain.replace(/_/g, " ")}</span>
                <span className="font-mono text-emerald-400">
                  {pct(stats.composite_pass_at_1)} · {stats.scenario_count} scenarios
                </span>
              </div>
            ))}
          </div>

          <div className="mt-10 flex flex-wrap gap-4 border-t border-white/10 pt-8 text-xs text-white/40">
            <span>Certificate ID: <strong className="text-white/70">{CERT_ID}</strong></span>
            <span>Benchmark date: <strong className="text-white/70">{benchmark.benchmark_date}</strong></span>
            <span>Dataset: <a href="https://huggingface.co/datasets/ServiceNow-AI/eva-bench" className="text-cyan-400 underline">EVA-Bench</a></span>
          </div>

          <p className="mt-6 text-[10px] leading-relaxed text-white/30">
            Independent certification by VoiceIQ EVA. Not affiliated with Retell AI, Inc. or ServiceNow.
            Verify at {VERIFY_URL}
          </p>
        </motion.div>

        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link
            href="/portal"
            className="rounded-full bg-gradient-to-r from-cyan-500 to-orange-500 px-6 py-3 text-[10px] font-bold uppercase tracking-widest"
          >
            Run your own prompt
          </Link>
          <a
            href={linkedInUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-white/20 px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-white/70 hover:text-white"
          >
            Share on LinkedIn
          </a>
          <Link
            href="/retell"
            className="rounded-full border border-cyan-500/40 px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-cyan-400"
          >
            Why Retell should care
          </Link>
        </div>
      </main>
    </div>
  )
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div
      className={`rounded-2xl border p-5 ${
        highlight
          ? "border-emerald-500/40 bg-emerald-500/10"
          : "border-white/10 bg-white/5"
      }`}
    >
      <p className="text-[10px] uppercase tracking-widest text-white/40">{label}</p>
      <p className={`mt-1 text-3xl font-black ${highlight ? "text-emerald-400" : ""}`}>
        {value}
      </p>
    </div>
  )
}

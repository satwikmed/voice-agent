"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { MeshGradient } from "@paper-design/shaders-react"
import benchmark from "@/data/eva-benchmark-results.json"

const LINKS = {
  portal: "/portal",
  cert: "/cert",
  github: "https://github.com/satwikmed/voice-agent",
  hfSpace: "https://huggingface.co/spaces/satwikmed/voiceiq-eva",
  evaBench: "https://huggingface.co/datasets/ServiceNow-AI/eva-bench",
  assure: "https://www.retellai.com",
}

const TIMELINE = [
  {
    phase: "01 · BUILD",
    title: "Write your Retell agent prompt",
    body: "Domain LLM + tools + voice settings. You think you're done.",
    color: "text-white/50",
  },
  {
    phase: "02 · VoiceIQ EVA",
    title: "Pre-launch torture test",
    body: "15 EVA-Bench enterprise scenarios. Simulated callers with real NPIs, PINs, ticket IDs. EVA-A + EVA-X scoring. Deploy gate.",
    color: "text-cyan-400",
    highlight: true,
  },
  {
    phase: "03 · SHIP",
    title: "Go live on Retell",
    body: "Phone number live. Real humans calling. No undo button.",
    color: "text-white/50",
  },
  {
    phase: "04 · Retell Assure",
    title: "Post-launch QA",
    body: "Monitor production calls. Catch regressions. The other half of the loop.",
    color: "text-orange-400",
  },
]

const ROAST = [
  {
    before: "Caller gives fake NPI. Agent loops. Everyone hangs up.",
    after: "Caller facts injected from EVA database. Auth in 2 turns.",
    domain: "Healthcare HR",
  },
  {
    before: "Agent offers flight that doesn't exist. EVA-A: 0.12.",
    after: "Backend state + resolution script. 100% airline pass.",
    domain: "Airline CSM",
  },
  {
    before: "Datadog call gets Wi-Fi troubleshooting script.",
    after: "Scenario-specific ITSM scripts. Adversarial denials pass.",
    domain: "Enterprise ITSM",
  },
]

export default function RetellPitchPage() {
  const summary = benchmark.summary
  const pct = (n: number) => `${(n * 100).toFixed(0)}%`

  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-white">
      <div className="pointer-events-none absolute inset-0">
        <MeshGradient
          className="h-full w-full opacity-40"
          colors={["#000000", "#06b6d4", "#164e63", "#f97316", "#000000"]}
          speed={0.12}
        />
      </div>

      <header className="relative z-20 mx-auto flex max-w-6xl items-center justify-between px-8 py-6">
        <Link href="/" className="text-xs uppercase tracking-widest text-white/40 hover:text-white">
          VoiceIQ
        </Link>
        <div className="flex gap-4">
          <Link href={LINKS.cert} className="text-xs uppercase tracking-widest text-emerald-400">
            EVA Certified ↗
          </Link>
          <Link
            href={LINKS.portal}
            className="rounded-full border border-white/20 px-4 py-2 text-[10px] font-bold uppercase tracking-widest"
          >
            Open portal
          </Link>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-6xl space-y-24 px-8 pb-32 pt-8">
        {/* Hero */}
        <section className="text-center">
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-[10px] font-bold uppercase tracking-[0.4em] text-cyan-400"
          >
            Open-source · Not affiliated with Retell AI
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 text-5xl font-black leading-[0.95] tracking-tight md:text-7xl"
          >
            Retell Assure catches failures
            <br />
            <span className="bg-gradient-to-r from-cyan-400 to-orange-400 bg-clip-text text-transparent">
              after launch.
            </span>
            <br />
            Who catches them before?
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="mx-auto mt-8 max-w-2xl text-lg text-white/55"
          >
            <strong className="text-white">VoiceIQ EVA</strong> is the missing pre-launch layer — EVA-Bench
            enterprise scenarios, EVA-A/EVA-X scoring, and a deploy gate for voice-agent prompts.
            Built to plug into the Retell ecosystem, not compete with it.
          </motion.p>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
            className="mt-10 flex flex-wrap justify-center gap-4"
          >
            <Link
              href={LINKS.cert}
              className="rounded-xl bg-emerald-500/20 px-8 py-4 text-xs font-bold uppercase tracking-widest text-emerald-300 ring-1 ring-emerald-500/40"
            >
              🏆 View EVA Certificate — {pct(summary.composite_pass_at_1)} pass
            </Link>
            <Link
              href={`${LINKS.portal}?tab=voiceiq-eva`}
              className="rounded-xl bg-gradient-to-r from-cyan-500 to-orange-500 px-8 py-4 text-xs font-bold uppercase tracking-widest"
            >
              Challenge your prompt
            </Link>
          </motion.div>
        </section>

        {/* The gap */}
        <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-10 backdrop-blur-md">
          <h2 className="text-center text-2xl font-bold">The Assure Gap</h2>
          <div className="mt-10 grid gap-4 md:grid-cols-2">
            <GapCard
              title="Without VoiceIQ EVA"
              items={[
                "Agent sounds great in demo",
                "Ships to production",
                "Healthcare auth loops on call #1",
                "Assure flags it post-launch",
                "Customer already churned",
              ]}
              bad
            />
            <GapCard
              title="With VoiceIQ EVA"
              items={[
                "15 EVA scenarios before launch",
                "Grounded backend + caller facts",
                "EVA-A / EVA-X composite gate",
                "Block deploy below 60% pass",
                "Assure monitors clean production",
              ]}
            />
          </div>
        </section>

        {/* Timeline */}
        <section>
          <h2 className="mb-10 text-center text-2xl font-bold">Full quality loop</h2>
          <div className="grid gap-4 md:grid-cols-4">
            {TIMELINE.map((step, i) => (
              <motion.div
                key={step.phase}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                viewport={{ once: true }}
                className={`rounded-2xl border p-6 ${
                  step.highlight
                    ? "border-cyan-500/40 bg-cyan-500/10"
                    : "border-white/10 bg-white/5"
                }`}
              >
                <p className={`text-[10px] font-bold uppercase tracking-widest ${step.color}`}>
                  {step.phase}
                </p>
                <p className="mt-3 font-semibold">{step.title}</p>
                <p className="mt-2 text-xs leading-relaxed text-white/50">{step.body}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Before / after roast */}
        <section>
          <h2 className="mb-2 text-center text-2xl font-bold">What broke — and what we fixed</h2>
          <p className="mb-10 text-center text-sm text-white/40">
            Same model. Same prompts. Different grounding. 33% → 100% composite pass.
          </p>
          <div className="space-y-6">
            {ROAST.map((r) => (
              <div
                key={r.domain}
                className="grid gap-4 rounded-2xl border border-white/10 bg-black/40 p-6 md:grid-cols-[1fr_auto_1fr]"
              >
                <div>
                  <p className="text-[10px] uppercase text-red-400/80">Before</p>
                  <p className="mt-1 text-sm text-white/60">{r.before}</p>
                </div>
                <div className="hidden self-center text-2xl text-white/20 md:block">→</div>
                <div>
                  <p className="text-[10px] uppercase text-emerald-400/80">After · {r.domain}</p>
                  <p className="mt-1 text-sm text-white/80">{r.after}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Stats strip */}
        <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {[
            { label: "Scenarios", value: "15" },
            { label: "Composite pass", value: pct(summary.composite_pass_at_1) },
            { label: "Avg EVA-A", value: pct(summary.avg_eva_a) },
            { label: "Domains", value: "3" },
          ].map((s) => (
            <div
              key={s.label}
              className="rounded-2xl border border-white/10 bg-white/5 p-6 text-center"
            >
              <p className="text-3xl font-black text-cyan-400">{s.value}</p>
              <p className="mt-1 text-[10px] uppercase tracking-widest text-white/40">{s.label}</p>
            </div>
          ))}
        </section>

        {/* CTA for Retell */}
        <section className="rounded-3xl border border-orange-500/30 bg-gradient-to-br from-orange-500/10 to-transparent p-12 text-center">
          <p className="text-[10px] font-bold uppercase tracking-[0.35em] text-orange-400">
            For the Retell team
          </p>
          <h2 className="mt-4 text-3xl font-bold">
            I built the pre-launch half of your QA story.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-sm text-white/55">
            Open-source adapter for EVA-Bench. Live demo, certificate, HF Space, GitHub.
            Happy to walk through findings or contribute to your ecosystem.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <a
              href={LINKS.github}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full border border-white/20 px-6 py-3 text-[10px] font-bold uppercase tracking-widest"
            >
              GitHub
            </a>
            <a
              href={LINKS.hfSpace}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full border border-white/20 px-6 py-3 text-[10px] font-bold uppercase tracking-widest"
            >
              HF Space
            </a>
            <a
              href={LINKS.evaBench}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full border border-white/20 px-6 py-3 text-[10px] font-bold uppercase tracking-widest"
            >
              EVA-Bench dataset
            </a>
            <Link
              href={LINKS.cert}
              className="rounded-full bg-emerald-500/30 px-6 py-3 text-[10px] font-bold uppercase tracking-widest text-emerald-200"
            >
              Verify certificate
            </Link>
          </div>
        </section>
      </main>
    </div>
  )
}

function GapCard({
  title,
  items,
  bad,
}: {
  title: string
  items: string[]
  bad?: boolean
}) {
  return (
    <div
      className={`rounded-2xl border p-8 ${
        bad ? "border-red-500/20 bg-red-500/5" : "border-emerald-500/20 bg-emerald-500/5"
      }`}
    >
      <p className={`text-sm font-bold ${bad ? "text-red-300" : "text-emerald-300"}`}>{title}</p>
      <ul className="mt-4 space-y-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-sm text-white/60">
            <span>{bad ? "✗" : "✓"}</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

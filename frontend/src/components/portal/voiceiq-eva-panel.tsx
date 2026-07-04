"use client"

import { useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import {
  aggregateEvaBenchmark,
  DOMAIN_AGENT_PROMPTS,
  evaluateEvaDeployGate,
  type EvaBenchmarkSummary,
  type EvaRunResult,
  type EvaScenario,
} from "@/lib/voiceiq-eva"
import { downloadRetellExport } from "@/lib/retell-export"
import Link from "next/link"

interface VoiceIQEvaPanelProps {
  agentPrompt: string
  onImportDomainPrompt: (prompt: string) => void
}

const DOMAINS = [
  { id: "all", label: "All domains (15)" },
  { id: "airline_csm", label: "Airline (5)" },
  { id: "healthcare_hrsd", label: "Healthcare HR (5)" },
  { id: "enterprise_itsm", label: "Enterprise ITSM (5)" },
] as const

export function VoiceIQEvaPanel({
  agentPrompt,
  onImportDomainPrompt,
}: VoiceIQEvaPanelProps) {
  const [scenarios, setScenarios] = useState<EvaScenario[]>([])
  const [selectedDomain, setSelectedDomain] = useState<string>("all")
  const [selectedEvaId, setSelectedEvaId] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [seedSummary, setSeedSummary] = useState<EvaBenchmarkSummary | null>(null)
  const [liveRuns, setLiveRuns] = useState<EvaRunResult[] | null>(null)
  const [keyFindings, setKeyFindings] = useState<string[]>([])
  const [usedSeed, setUsedSeed] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [scenariosRes, benchmarkRes] = await Promise.all([
          fetch("/api/voiceiq-eva/scenarios"),
          fetch("/api/voiceiq-eva/benchmark"),
        ])
        const scenariosPayload = await scenariosRes.json()
        const benchmarkPayload = await benchmarkRes.json()
        setScenarios(scenariosPayload.scenarios || [])
        setSeedSummary(benchmarkPayload.summary || null)
        setKeyFindings(benchmarkPayload.key_findings || [])
        if (scenariosPayload.scenarios?.[0]) {
          setSelectedEvaId(scenariosPayload.scenarios[0].eva_id)
        }
      } catch (err) {
        console.error(err)
        setError("Failed to load EVA-Bench scenarios.")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const filteredScenarios = useMemo(() => {
    if (selectedDomain === "all") return scenarios
    return scenarios.filter((s) => s.domain === selectedDomain)
  }, [scenarios, selectedDomain])

  const activeSummary = useMemo(() => {
    if (liveRuns && liveRuns.length > 0) return aggregateEvaBenchmark(liveRuns)
    return seedSummary
  }, [liveRuns, seedSummary])

  const deployGate = useMemo(
    () => (activeSummary ? evaluateEvaDeployGate(activeSummary) : null),
    [activeSummary]
  )

  const selectedScenario = scenarios.find((s) => s.eva_id === selectedEvaId)

  const runBenchmark = async (mode: "single" | "suite") => {
    setRunning(true)
    setError(null)
    try {
      const response = await fetch("/api/voiceiq-eva/benchmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          eva_id: mode === "single" ? selectedEvaId : undefined,
          domain: mode === "suite" && selectedDomain !== "all" ? selectedDomain : undefined,
          limit: mode === "suite" ? 5 : 1,
          agent_prompt: agentPrompt,
        }),
      })
      const data = await response.json()
      if (data.detail && !data.runs && !data.seeded) {
        throw new Error(data.detail)
      }
      if (data.runs) {
        setLiveRuns(data.runs)
        setKeyFindings(data.key_findings || [])
        setUsedSeed(Boolean(data.seeded))
      } else if (data.seeded) {
        setUsedSeed(true)
        setKeyFindings(data.key_findings || [])
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Benchmark failed.")
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return <p className="text-center text-xs text-white/50">Loading VoiceIQ EVA…</p>
  }

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl space-y-2">
            <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-400">
              VoiceIQ EVA · Hugging Face EVA-Bench
            </p>
            <h2 className="text-2xl font-bold">
              Pre-launch QA on enterprise voice scenarios
            </h2>
            <p className="text-sm text-white/60 leading-relaxed">
              Runs Retell-style agent prompts against{" "}
              <a
                href="https://huggingface.co/datasets/ServiceNow-AI/eva-bench"
                target="_blank"
                rel="noopener noreferrer"
                className="text-cyan-400 underline"
              >
                ServiceNow EVA-Bench
              </a>{" "}
              — 15 curated scenarios across airline, healthcare HR, and ITSM.
              Scores EVA-A (accuracy) and EVA-X (experience). Complements{" "}
              <span className="text-white/80">Retell Assure</span> post-launch QA.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/cert"
              className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-300"
            >
              🏆 EVA Certified
            </Link>
            {DOMAINS.map((d) => (
              <button
                key={d.id}
                onClick={() => setSelectedDomain(d.id)}
                className={`rounded-full px-3 py-1 text-[10px] uppercase tracking-wider ${
                  selectedDomain === d.id
                    ? "bg-cyan-500/30 text-cyan-200"
                    : "bg-white/5 text-white/60 hover:text-white"
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {activeSummary && deployGate && (
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-2xl border p-6 ${
            deployGate.passed
              ? "border-emerald-500/30 bg-emerald-500/10"
              : "border-orange-500/30 bg-orange-500/10"
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-white/50">
                EVA Deploy Gate {usedSeed ? "(seeded demo)" : "(live run)"}
              </p>
              <p className="text-xl font-bold">
                {deployGate.passed ? "Ready for production" : "Blocked — tune prompts"}
              </p>
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <Metric label="EVA-A pass@1" value={activeSummary.eva_a_pass_at_1} />
              <Metric label="EVA-X pass@1" value={activeSummary.eva_x_pass_at_1} />
              <Metric label="Composite" value={activeSummary.composite_pass_at_1} />
            </div>
          </div>
          {!deployGate.passed && (
            <ul className="mt-4 space-y-1 text-xs text-orange-200/90">
              {deployGate.blockers.map((b) => (
                <li key={b}>• {b}</li>
              ))}
            </ul>
          )}
        </motion.section>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-white/10 bg-black/40 p-6">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-white/70">
            Scenario
          </h3>
          <select
            value={selectedEvaId}
            onChange={(e) => setSelectedEvaId(e.target.value)}
            className="mb-4 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm"
          >
            {filteredScenarios.map((s) => (
              <option key={s.eva_id} value={s.eva_id} className="bg-black">
                {s.eva_id} — {s.domain_label}
              </option>
            ))}
          </select>

          {selectedScenario && (
            <div className="space-y-3 text-xs text-white/60">
              <p>{selectedScenario.scenario_description.slice(0, 280)}…</p>
              <p>
                <span className="text-white/40">Tool density:</span>{" "}
                {selectedScenario.tool_density} ·{" "}
                <span className="text-white/40">Difficulty:</span>{" "}
                {selectedScenario.difficulty_level}
              </p>
              <button
                onClick={() =>
                  onImportDomainPrompt(DOMAIN_AGENT_PROMPTS[selectedScenario.domain])
                }
                className="text-cyan-400 underline"
              >
                Import domain voice-agent prompt
              </button>
              <button
                onClick={() =>
                  downloadRetellExport(
                    agentPrompt || DOMAIN_AGENT_PROMPTS[selectedScenario.domain],
                    selectedScenario.domain,
                    `voiceiq-eva-${selectedScenario.domain}.json`
                  )
                }
                className="ml-4 text-orange-400 underline"
              >
                Export Retell LLM JSON
              </button>
            </div>
          )}

          <div className="mt-6 flex flex-wrap gap-2">
            <button
              disabled={running}
              onClick={() => runBenchmark("single")}
              className="rounded-full bg-gradient-to-r from-cyan-500 to-orange-500 px-4 py-2 text-[10px] font-bold uppercase tracking-wider disabled:opacity-50"
            >
              {running ? "Running…" : "Run 1 scenario"}
            </button>
            <button
              disabled={running}
              onClick={() => runBenchmark("suite")}
              className="rounded-full border border-white/20 px-4 py-2 text-[10px] font-bold uppercase tracking-wider disabled:opacity-50"
            >
              Run domain suite
            </button>
          </div>
          {error && <p className="mt-3 text-xs text-red-400">{error}</p>}
        </section>

        <section className="rounded-2xl border border-white/10 bg-black/40 p-6">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-white/70">
            Domain breakdown
          </h3>
          {activeSummary &&
            Object.entries(activeSummary.by_domain).map(([domain, stats]) => (
              <div
                key={domain}
                className="mb-4 rounded-lg border border-white/5 bg-white/5 p-4"
              >
                <p className="text-xs font-medium text-white/80">{domain}</p>
                <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-white/50">
                  <span>EVA-A avg: {(stats.avg_eva_a * 100).toFixed(0)}%</span>
                  <span>EVA-X avg: {(stats.avg_eva_x * 100).toFixed(0)}%</span>
                  <span>Pass@1: {(stats.composite_pass_at_1 * 100).toFixed(0)}%</span>
                  <span>Scenarios: {stats.scenario_count}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-orange-500"
                    style={{ width: `${stats.composite_pass_at_1 * 100}%` }}
                  />
                </div>
              </div>
            ))}
        </section>
      </div>

      {keyFindings.length > 0 && (
        <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-white/70">
            Key findings
          </h3>
          <ul className="space-y-2 text-sm text-white/70">
            {keyFindings.map((f) => (
              <li key={f}>• {f}</li>
            ))}
          </ul>
        </section>
      )}

      {liveRuns && liveRuns.length > 0 && (
        <section className="rounded-2xl border border-white/10 bg-black/40 p-6">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-white/70">
            Latest run results
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-white/40">
                <tr>
                  <th className="pb-2 pr-4">Scenario</th>
                  <th className="pb-2 pr-4">EVA-A</th>
                  <th className="pb-2 pr-4">EVA-X</th>
                  <th className="pb-2">Pass</th>
                </tr>
              </thead>
              <tbody className="text-white/70">
                {liveRuns.map((run) => (
                  <tr key={run.eva_id} className="border-t border-white/5">
                    <td className="py-2 pr-4">{run.eva_id}</td>
                    <td className="py-2 pr-4">{(run.eva_a * 100).toFixed(0)}%</td>
                    <td className="py-2 pr-4">{(run.eva_x * 100).toFixed(0)}%</td>
                    <td className="py-2">
                      {run.composite_pass ? (
                        <span className="text-emerald-400">✓</span>
                      ) : (
                        <span className="text-orange-400">✗</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-[10px] uppercase text-white/40">{label}</p>
      <p className="text-lg font-bold">{(value * 100).toFixed(0)}%</p>
    </div>
  )
}

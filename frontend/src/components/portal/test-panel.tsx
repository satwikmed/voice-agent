"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { PulsingBorder } from "@paper-design/shaders-react"
import { SimulationResultView } from "@/components/portal/simulation-result"
import type { RunDetail, Scenario, SimulationResult, TestRun } from "@/lib/types"
import { saveCustomRun, saveSuiteResults, type SuiteResultSummary } from "@/lib/run-storage"

interface TestPanelProps {
  scenarios: Scenario[]
  agentPrompt: string
  onAgentPromptChange: (prompt: string) => void
  selectedScenarioId: number
  onScenarioChange: (id: number) => void
  onRunsUpdated: (runs: TestRun[]) => void
  onSuiteComplete: (results: SuiteResultSummary[]) => void
}

export function TestPanel({
  scenarios,
  agentPrompt,
  onAgentPromptChange,
  selectedScenarioId,
  onScenarioChange,
  onRunsUpdated,
  onSuiteComplete,
}: TestPanelProps) {
  const [running, setRunning] = useState<"one" | "all" | null>(null)
  const [progress, setProgress] = useState(0)
  const [currentScenario, setCurrentScenario] = useState<string | null>(null)
  const [singleResult, setSingleResult] = useState<SimulationResult | null>(null)
  const [suiteResults, setSuiteResults] = useState<SuiteResultSummary[]>([])
  const [error, setError] = useState<string | null>(null)

  const runOne = async () => {
    setRunning("one")
    setError(null)
    setSingleResult(null)
    setSuiteResults([])

    try {
      const data = await postSimulate(agentPrompt, selectedScenarioId)
      setSingleResult(data)
      persistSingleRun(data, selectedScenarioId)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Simulation failed.")
    } finally {
      setRunning(null)
    }
  }

  const runAll = async () => {
    setRunning("all")
    setError(null)
    setSingleResult(null)
    setSuiteResults([])
    setProgress(0)

    const collected: SuiteResultSummary[] = []
    const fullResults: Parameters<typeof saveSuiteResults>[0] = []

    try {
      for (let i = 0; i < scenarios.length; i++) {
        const scenario = scenarios[i]
        setCurrentScenario(scenario.scenario_name)
        const data = await postSimulate(agentPrompt, scenario.id)

        collected.push({
          scenario_id: scenario.id,
          scenario_name: scenario.scenario_name,
          difficulty_level: scenario.difficulty_level,
          overall_score: data.overall_score,
          goal_completed: data.goal_completed,
          total_turns: data.total_turns,
        })
        fullResults.push({
          ...collected[collected.length - 1],
          transcript: data.transcript,
          scores_breakdown: data.scores_breakdown,
          failure_points: data.failure_points,
          recommendations: data.recommendations,
        })

        setSuiteResults([...collected])
        setProgress(Math.round(((i + 1) / scenarios.length) * 100))
      }

      const runs = saveSuiteResults(fullResults, agentPrompt)
      onRunsUpdated(runs)
      onSuiteComplete(collected)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Suite run failed.")
    } finally {
      setRunning(null)
      setCurrentScenario(null)
    }
  }

  async function postSimulate(prompt: string, scenarioId: number) {
    const response = await fetch("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent_prompt: prompt, scenario_id: scenarioId }),
    })
    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || "Simulation failed")
    }
    return response.json() as Promise<SimulationResult>
  }

  function persistSingleRun(data: SimulationResult, scenarioId: number) {
    const scenario = scenarios.find((s) => s.id === scenarioId)
    const detail: RunDetail = {
      id: data.run_id,
      scenario_id: scenarioId,
      scenario_name: scenario?.scenario_name || "Unknown",
      difficulty_level: scenario?.difficulty_level || "medium",
      overall_score: data.overall_score,
      total_turns: data.total_turns,
      goal_completed: data.goal_completed ? 1 : 0,
      created_at: new Date().toISOString(),
      agent_system_prompt: agentPrompt,
      conversation_transcript: data.transcript,
      scores_breakdown: data.scores_breakdown,
      failure_points: data.failure_points,
      recommendations: data.recommendations.join("\n"),
      source: "simulation",
    }
    const run: TestRun = {
      id: detail.id,
      scenario_id: detail.scenario_id,
      scenario_name: detail.scenario_name,
      difficulty_level: detail.difficulty_level,
      overall_score: detail.overall_score,
      total_turns: detail.total_turns,
      goal_completed: detail.goal_completed,
      created_at: detail.created_at,
      source: "simulation",
    }
    const { runs } = saveCustomRun(run, detail)
    onRunsUpdated(runs)
  }

  const suitePassed = suiteResults.filter((r) => r.overall_score >= 70).length
  const busy = running !== null

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div className="space-y-5 lg:col-span-1">
        <div className="rounded-2xl border border-white/10 bg-black/40 p-6 backdrop-blur-md">
          <h3 className="border-b border-white/10 pb-3 text-sm font-semibold">
            Run tests
          </h3>

          <label className="mt-4 block text-xs text-white/50">Scenario</label>
          <select
            value={selectedScenarioId}
            onChange={(e) => onScenarioChange(parseInt(e.target.value))}
            disabled={busy}
            className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs text-white"
          >
            {scenarios.map((s) => (
              <option key={s.id} value={s.id} className="bg-black">
                {s.scenario_name} ({s.difficulty_level})
              </option>
            ))}
          </select>

          <label className="mt-4 block text-xs text-white/50">Agent prompt</label>
          <textarea
            value={agentPrompt}
            onChange={(e) => onAgentPromptChange(e.target.value)}
            disabled={busy}
            rows={7}
            className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 p-3 font-mono text-xs text-white"
          />

          <div className="mt-4 flex flex-col gap-2">
            <button
              onClick={runOne}
              disabled={busy}
              className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 py-2.5 text-xs font-bold uppercase tracking-widest text-cyan-300 disabled:opacity-50"
            >
              {running === "one" ? "Running…" : "▶ Run selected"}
            </button>
            <button
              onClick={runAll}
              disabled={busy}
              className="rounded-xl bg-gradient-to-r from-cyan-500 to-orange-500 py-2.5 text-xs font-bold uppercase tracking-widest text-white disabled:opacity-50"
            >
              {running === "all" ? "Running suite…" : `▶ Run all ${scenarios.length}`}
            </button>
          </div>

          {error && (
            <p className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
              {error}
            </p>
          )}
        </div>

        <div className="rounded-2xl border border-white/10 bg-black/40 p-4 backdrop-blur-md">
          <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-white/40">
            Scenario library
          </p>
          <div className="max-h-48 space-y-2 overflow-y-auto">
            {scenarios.map((s) => (
              <button
                key={s.id}
                onClick={() => onScenarioChange(s.id)}
                className={`w-full rounded-lg border px-3 py-2 text-left text-xs transition ${
                  selectedScenarioId === s.id
                    ? "border-cyan-500/40 bg-cyan-500/10"
                    : "border-white/5 bg-white/5 hover:bg-white/10"
                }`}
              >
                <span className="font-medium">{s.scenario_name}</span>
                <span className="ml-2 text-white/40">{s.difficulty_level}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="lg:col-span-2">
        <AnimatePresence mode="wait">
          {running === "all" ? (
            <motion.div
              key="suite-running"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex h-[480px] flex-col items-center justify-center rounded-2xl border border-white/10 bg-black/30 p-8 text-center"
            >
              <PulsingBorder
                colors={["#06b6d4", "#f97316"]}
                colorBack="#00000000"
                speed={1.5}
                roundness={1}
                thickness={0.1}
                intensity={4}
                spots={4}
                style={{ width: "48px", height: "48px" }}
              />
              <h4 className="mt-6 text-sm font-bold">Suite in progress</h4>
              <p className="mt-2 text-xs text-white/50">{currentScenario}</p>
              <div className="mt-6 h-2 w-full max-w-md overflow-hidden rounded-full bg-white/10">
                <motion.div
                  className="h-full bg-gradient-to-r from-cyan-500 to-orange-500"
                  animate={{ width: `${progress}%` }}
                />
              </div>
              <p className="mt-2 font-mono text-xs text-cyan-400">{progress}%</p>
            </motion.div>
          ) : singleResult ? (
            <motion.div key="single" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <SimulationResultView result={singleResult} />
            </motion.div>
          ) : suiteResults.length > 0 ? (
            <motion.div
              key="suite-done"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-2xl border border-white/10 bg-black/30 p-6"
            >
              <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <h4 className="text-lg font-bold">Suite complete</h4>
                  <p className="text-xs text-white/50">
                    {suitePassed}/{suiteResults.length} passed at 70+
                  </p>
                </div>
                <span className="text-2xl font-black text-cyan-400">
                  {Math.round((suitePassed / suiteResults.length) * 100)}%
                </span>
              </div>
              <div className="max-h-[400px] space-y-2 overflow-y-auto">
                {suiteResults.map((r) => (
                  <div
                    key={r.scenario_id}
                    className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-medium">{r.scenario_name}</p>
                      <p className="text-[10px] text-white/40">
                        {r.difficulty_level} · {r.total_turns} turns
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-bold ${
                        r.overall_score >= 70
                          ? "bg-emerald-500/15 text-emerald-400"
                          : "bg-red-500/15 text-red-400"
                      }`}
                    >
                      {r.overall_score.toFixed(0)}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex h-[480px] items-center justify-center rounded-2xl border border-dashed border-white/10 p-8 text-center text-white/40"
            >
              <p className="max-w-sm text-xs">
                Run one scenario or the full suite. Results appear here and sync to
                History and Coverage.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

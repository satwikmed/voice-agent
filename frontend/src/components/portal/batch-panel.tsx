"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { PulsingBorder } from "@paper-design/shaders-react"
import type { Scenario } from "@/lib/types"

interface BatchPanelProps {
  scenarios: Scenario[]
  agentPrompt: string
  onComplete: (results: BatchResult[]) => void
}

export interface BatchResult {
  scenario_id: number
  scenario_name: string
  difficulty_level: string
  overall_score: number
  goal_completed: boolean
  total_turns: number
}

export function BatchPanel({
  scenarios,
  agentPrompt,
  onComplete,
}: BatchPanelProps) {
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentScenario, setCurrentScenario] = useState<string | null>(null)
  const [results, setResults] = useState<BatchResult[]>([])
  const [error, setError] = useState<string | null>(null)

  const runSuite = async () => {
    setRunning(true)
    setError(null)
    setResults([])
    setProgress(0)

    const collected: BatchResult[] = []

    try {
      for (let i = 0; i < scenarios.length; i++) {
        const scenario = scenarios[i]
        setCurrentScenario(scenario.scenario_name)

        const response = await fetch("/api/simulate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            agent_prompt: agentPrompt,
            scenario_id: scenario.id,
          }),
        })

        if (!response.ok) {
          const err = await response.json()
          throw new Error(err.detail || `Failed on ${scenario.scenario_name}`)
        }

        const data = await response.json()
        collected.push({
          scenario_id: scenario.id,
          scenario_name: scenario.scenario_name,
          difficulty_level: scenario.difficulty_level,
          overall_score: data.overall_score,
          goal_completed: data.goal_completed,
          total_turns: data.total_turns,
        })

        setResults([...collected])
        setProgress(Math.round(((i + 1) / scenarios.length) * 100))
      }

      onComplete(collected)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Batch suite failed.")
    } finally {
      setRunning(false)
      setCurrentScenario(null)
    }
  }

  const passed = results.filter((r) => r.overall_score >= 70).length

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div className="space-y-6 rounded-2xl border border-white/10 bg-black/40 p-6 backdrop-blur-md lg:col-span-1">
        <h3 className="border-b border-white/10 pb-3 text-sm font-semibold tracking-wide">
          Full test suite
        </h3>
        <p className="text-xs leading-relaxed text-white/50">
          Runs all {scenarios.length} scenarios sequentially — mock caller, agent
          loop, LLM judge on each. Typical runtime: 3–5 minutes.
        </p>
        <button
          onClick={runSuite}
          disabled={running}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-orange-500 py-3 text-xs font-bold uppercase tracking-widest text-white transition hover:shadow-lg disabled:opacity-50"
        >
          {running ? "Running suite…" : "▶ Run all scenarios"}
        </button>
        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
            {error}
          </div>
        )}
      </div>

      <div className="space-y-6 lg:col-span-2">
        <AnimatePresence mode="wait">
          {running ? (
            <motion.div
              key="running"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex h-[420px] flex-col items-center justify-center rounded-2xl border border-white/10 bg-black/30 p-8 text-center backdrop-blur-md"
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
              <h4 className="mt-6 text-sm font-bold">Batch suite in progress</h4>
              <p className="mt-2 text-xs text-white/50">
                {currentScenario
                  ? `Evaluating: ${currentScenario}`
                  : "Starting…"}
              </p>
              <div className="mt-6 h-2 w-full max-w-md overflow-hidden rounded-full bg-white/10">
                <motion.div
                  className="h-full bg-gradient-to-r from-cyan-500 to-orange-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
              <p className="mt-2 font-mono text-xs text-cyan-400">{progress}%</p>
            </motion.div>
          ) : results.length > 0 ? (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-white/10 bg-black/30 p-6 backdrop-blur-md"
            >
              <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <h4 className="text-lg font-bold">Suite complete</h4>
                  <p className="text-xs text-white/50">
                    {passed}/{results.length} passed at 70+
                  </p>
                </div>
                <span className="text-2xl font-black text-cyan-400">
                  {Math.round((passed / results.length) * 100)}%
                </span>
              </div>
              <div className="max-h-[340px] space-y-2 overflow-y-auto">
                {results.map((result) => (
                  <div
                    key={result.scenario_id}
                    className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-medium">{result.scenario_name}</p>
                      <p className="text-[10px] text-white/40">
                        {result.difficulty_level} · {result.total_turns} turns ·{" "}
                        {result.goal_completed ? "goal met" : "hangup/fail"}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-bold ${
                        result.overall_score >= 70
                          ? "bg-emerald-500/15 text-emerald-400"
                          : "bg-red-500/15 text-red-400"
                      }`}
                    >
                      {result.overall_score.toFixed(0)}
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
              className="flex h-[420px] flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 p-8 text-center text-white/30"
            >
              <p className="text-sm text-white/50">No batch run yet</p>
              <p className="mt-2 max-w-sm text-xs">
                Run the full suite to populate deploy gate, coverage heatmap, and
                history in one shot.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

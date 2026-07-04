"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { MeshGradient } from "@paper-design/shaders-react"
import { DeployGateBanner } from "@/components/portal/deploy-gate-banner"
import { CoveragePanel } from "@/components/portal/coverage-panel"
import { RetellPanel } from "@/components/portal/retell-panel"
import { VoiceIQEvaPanel } from "@/components/portal/voiceiq-eva-panel"
import { TestPanel } from "@/components/portal/test-panel"
import { CalibrationPanel } from "@/components/portal/calibration-panel"
import { HistoryPanel } from "@/components/portal/history-panel"
import { evaluateDeployGate } from "@/lib/deploy-gate"
import { loadCustomRuns, type SuiteResultSummary } from "@/lib/run-storage"
import coverageCategories from "@/data/coverage-categories.json"
import type {
  CalibrationPair,
  CoverageCategory,
  Scenario,
  TestRun,
} from "@/lib/types"

type PortalTab = "test" | "voiceiq-eva" | "coverage" | "retell" | "calibration" | "history"

const TABS: PortalTab[] = ["test", "voiceiq-eva", "coverage", "retell", "calibration", "history"]

const TAB_LABELS: Record<PortalTab, string> = {
  test: "test",
  "voiceiq-eva": "VoiceIQ EVA",
  coverage: "coverage",
  retell: "retell",
  calibration: "calibration",
  history: "history",
}

const DEFAULT_PROMPT =
  "You are a Retell AI voice agent for TechFlow, a B2B SaaS platform.\n" +
  "Speak concisely like a phone agent — short sentences, no markdown.\n" +
  "Be helpful, professional, and empathetic. Answer questions directly.\n" +
  "Pricing: Starter $29/seat/mo, Professional $79/seat/mo, Enterprise $149/seat/mo.\n" +
  "If the caller is frustrated, acknowledge before troubleshooting.\n" +
  "Never promise refunds you cannot authorize — offer escalation paths instead."

export default function VoiceIQPortal() {
  const [activeTab, setActiveTab] = useState<PortalTab>("test")
  const [loading, setLoading] = useState(true)
  const [runs, setRuns] = useState<TestRun[]>([])
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [calibrationData, setCalibrationData] = useState<CalibrationPair[]>([])
  const [suiteResults, setSuiteResults] = useState<SuiteResultSummary[]>([])
  const [agentPrompt, setAgentPrompt] = useState(DEFAULT_PROMPT)
  const [selectedScenarioId, setSelectedScenarioId] = useState(1)

  useEffect(() => {
    async function init() {
      try {
        const [runsRes, scenariosRes, calibRes] = await Promise.all([
          fetch("/api/runs"),
          fetch("/api/scenarios"),
          fetch("/api/calibration"),
        ])
        const [seedRuns, scenariosData, calibData] = await Promise.all([
          runsRes.json(),
          scenariosRes.json(),
          calibRes.json(),
        ])
        setRuns([...loadCustomRuns(), ...seedRuns])
        setScenarios(scenariosData)
        setCalibrationData(calibData)
        if (scenariosData[0]) setSelectedScenarioId(scenariosData[0].id)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  const deployGate = useMemo(
    () =>
      evaluateDeployGate(
        scenarios,
        runs,
        suiteResults.map((r) => ({
          scenario_id: r.scenario_id,
          overall_score: r.overall_score,
        }))
      ),
    [scenarios, runs, suiteResults]
  )

  return (
    <div className="relative min-h-screen overflow-hidden bg-black pb-16 font-sans text-white">
      <div className="pointer-events-none absolute inset-0">
        <MeshGradient
          className="h-full w-full opacity-60"
          colors={["#000000", "#06b6d4", "#0891b2", "#164e63", "#f97316"]}
          speed={0.2}
        />
      </div>

      <header className="relative z-20 flex flex-col gap-4 border-b border-white/5 bg-black/30 px-8 py-6 backdrop-blur-md lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-xl font-bold">VoiceIQ</h1>
          <p className="text-[10px] uppercase tracking-wider text-white/50">
            Pre-launch eval for Retell voice agents
          </p>
        </div>
        <nav className="flex flex-wrap gap-1 rounded-full border border-white/10 bg-white/5 p-1">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-3 py-1.5 text-[10px] font-medium uppercase tracking-wider ${
                activeTab === tab
                  ? "bg-gradient-to-r from-cyan-500 to-orange-500 text-white"
                  : "text-white/70 hover:text-white"
              }`}
            >
              {TAB_LABELS[tab]}
            </button>
          ))}
        </nav>
        <Link href="/" className="text-[10px] uppercase text-white/40 hover:text-white">
          ← Home
        </Link>
      </header>

      <main className="relative z-10 mx-auto mt-10 max-w-7xl px-8">
        {loading ? (
          <p className="text-center text-xs text-white/50">Loading…</p>
        ) : (
          <>
            <DeployGateBanner gate={deployGate} />
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.25 }}
              >
                {activeTab === "test" && (
                  <TestPanel
                    scenarios={scenarios}
                    agentPrompt={agentPrompt}
                    onAgentPromptChange={setAgentPrompt}
                    selectedScenarioId={selectedScenarioId}
                    onScenarioChange={setSelectedScenarioId}
                    onRunsUpdated={setRuns}
                    onSuiteComplete={setSuiteResults}
                  />
                )}
                {activeTab === "voiceiq-eva" && (
                  <VoiceIQEvaPanel
                    agentPrompt={agentPrompt}
                    onImportDomainPrompt={setAgentPrompt}
                  />
                )}
                {activeTab === "coverage" && (
                  <CoveragePanel
                    categories={coverageCategories as CoverageCategory[]}
                    scenarios={scenarios}
                    runs={runs}
                  />
                )}
                {activeTab === "retell" && (
                  <RetellPanel
                    agentPrompt={agentPrompt}
                    onImportPrompt={setAgentPrompt}
                  />
                )}
                {activeTab === "calibration" && (
                  <CalibrationPanel calibrationData={calibrationData} />
                )}
                {activeTab === "history" && <HistoryPanel runs={runs} />}
              </motion.div>
            </AnimatePresence>
          </>
        )}
      </main>
    </div>
  )
}

"use client"
import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { MeshGradient, PulsingBorder } from "@paper-design/shaders-react"

// Types matching database schema
interface Scenario {
  id: number
  scenario_name: string
  scenario_description: string
  caller_personality: string
  caller_goal: string
  difficulty_level: string
}

interface TestRun {
  id: number
  scenario_id: number
  scenario_name: string
  difficulty_level: string
  overall_score: number
  total_turns: number
  goal_completed: number
  created_at: string
}

interface RunDetail extends TestRun {
  agent_system_prompt: string
  conversation_transcript: Array<{
    turn: number
    role: "agent" | "caller"
    content: string
  }>
  scores_breakdown: {
    response_relevance: number
    objection_handling: number
    conversation_flow: number
    empathy: number
    goal_completion: number
  }
  failure_points: Array<{
    turn: number
    reason: string
  }>
  recommendations: string
}

interface CalibrationPair {
  id: number
  test_run_id: number
  human_score: number
  judge_score: number
  score_delta: number
  notes: string
  scenario_name: string
}

export default function VoiceIQPortal() {
  const [activeTab, setActiveTab] = useState<"calibration" | "history" | "scenarios" | "simulate">("calibration")
  const [runs, setRuns] = useState<TestRun[]>([])
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [calibrationData, setCalibrationData] = useState<CalibrationPair[]>([])
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  // Live simulation states
  const [agentPrompt, setAgentPrompt] = useState<string>(
    "You are a professional AI sales representative for TechFlow, a B2B SaaS platform.\nBe helpful, professional, and empathetic. Answer questions directly.\nPricing: Starter $29/seat/mo, Professional $79/seat/mo, Enterprise $149/seat/mo."
  )
  const [selectedScenarioId, setSelectedScenarioId] = useState<number>(1)
  const [simulating, setSimulating] = useState<boolean>(false)
  const [simResult, setSimResult] = useState<any | null>(null)
  const [simError, setSimError] = useState<string | null>(null)

  const [selectedCalibId, setSelectedCalibId] = useState<number | null>(null)
  const [selectedCalibDetail, setSelectedCalibDetail] = useState<RunDetail | null>(null)

  // Fetch detailed run details for selected calibration pair
  useEffect(() => {
    if (selectedCalibId === null) return
    async function fetchCalibDetail() {
      try {
        const res = await fetch(`/api/runs/${selectedCalibId}`)
        const data = await res.json()
        setSelectedCalibDetail(data)
      } catch (err) {
        console.error(err)
      }
    }
    fetchCalibDetail()
  }, [selectedCalibId])

  // Fetch Core Database records
  useEffect(() => {
    async function initFetch() {
      try {
        const [runsRes, scenariosRes, calibRes] = await Promise.all([
          fetch("/api/runs"),
          fetch("/api/scenarios"),
          fetch("/api/calibration")
        ])
        
        const runsData = await runsRes.json()
        const scenariosData = await scenariosRes.json()
        const calibData = await calibRes.json()

        // Load custom runs from localStorage
        let localRuns: TestRun[] = []
        try {
          const stored = localStorage.getItem("voiceiq_custom_runs")
          if (stored) {
            localRuns = JSON.parse(stored)
          }
        } catch (e) {
          console.error("Failed to read custom runs", e)
        }

        const combinedRuns = [...localRuns, ...runsData]

        setRuns(combinedRuns)
        setScenarios(scenariosData)
        setCalibrationData(calibData)
        
        if (combinedRuns.length > 0) {
          setSelectedRunId(combinedRuns[0].id)
        }
        if (calibData.length > 0) {
          setSelectedCalibId(calibData[0].test_run_id)
        }
        if (scenariosData.length > 0) {
          setSelectedScenarioId(scenariosData[0].id)
        }
      } catch (err) {
        console.error("Failed to fetch API data", err)
      } finally {
        setLoading(false)
      }
    }
    initFetch()
  }, [])

  // Fetch Detailed Run Transcript
  useEffect(() => {
    if (selectedRunId === null) return

    // Check if it is a local storage run first
    let localDetails: RunDetail[] = []
    try {
      const stored = localStorage.getItem("voiceiq_custom_run_details")
      if (stored) {
        localDetails = JSON.parse(stored)
      }
    } catch (e) {
      console.error(e)
    }

    const found = localDetails.find(r => r.id === selectedRunId)
    if (found) {
      setRunDetail(found)
      return
    }

    async function fetchDetail() {
      try {
        const res = await fetch(`/api/runs/${selectedRunId}`)
        const data = await res.json()
        setRunDetail(data)
      } catch (err) {
        console.error(err)
      }
    }
    fetchDetail()
  }, [selectedRunId])

  // Statistical Metrics calculations for judge calibration
  const mae = calibrationData.length > 0 
    ? (calibrationData.reduce((acc, curr) => acc + Math.abs(curr.judge_score - curr.human_score), 0) / calibrationData.length).toFixed(1)
    : "N/A"
  
  const bias = calibrationData.length > 0
    ? (calibrationData.reduce((acc, curr) => acc + (curr.judge_score - curr.human_score), 0) / calibrationData.length).toFixed(1)
    : "N/A"

  const avgHumanScore = calibrationData.length > 0
    ? (calibrationData.reduce((acc, curr) => acc + curr.human_score, 0) / calibrationData.length).toFixed(1)
    : "N/A"

  const triggerSimulation = async () => {
    setSimulating(true)
    setSimResult(null)
    setSimError(null)
    try {
      const response = await fetch("/api/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agent_prompt: agentPrompt,
          scenario_id: selectedScenarioId
        })
      })
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || "Simulation run failed")
      }
      const data = await response.json()
      
      const newRunDetail: RunDetail = {
        id: data.run_id,
        scenario_id: selectedScenarioId,
        scenario_name: scenarios.find(s => s.id === selectedScenarioId)?.scenario_name || "Unknown Scenario",
        difficulty_level: scenarios.find(s => s.id === selectedScenarioId)?.difficulty_level || "medium",
        overall_score: data.overall_score,
        total_turns: data.total_turns,
        goal_completed: data.goal_completed ? 1 : 0,
        created_at: new Date().toISOString(),
        agent_system_prompt: agentPrompt,
        conversation_transcript: data.transcript,
        scores_breakdown: data.scores_breakdown,
        failure_points: data.failure_points,
        recommendations: data.recommendations.join("\n")
      }
      
      setSimResult(data)

      const newRunItem: TestRun = {
        id: newRunDetail.id,
        scenario_id: newRunDetail.scenario_id,
        scenario_name: newRunDetail.scenario_name,
        difficulty_level: newRunDetail.difficulty_level,
        overall_score: newRunDetail.overall_score,
        total_turns: newRunDetail.total_turns,
        goal_completed: newRunDetail.goal_completed,
        created_at: newRunDetail.created_at
      }

      try {
        const storedRuns = localStorage.getItem("voiceiq_custom_runs")
        const currentRuns: TestRun[] = storedRuns ? JSON.parse(storedRuns) : []
        const updatedRuns = [newRunItem, ...currentRuns]
        localStorage.setItem("voiceiq_custom_runs", JSON.stringify(updatedRuns))

        const storedDetails = localStorage.getItem("voiceiq_custom_run_details")
        const currentDetails: RunDetail[] = storedDetails ? JSON.parse(storedDetails) : []
        const updatedDetails = [newRunDetail, ...currentDetails]
        localStorage.setItem("voiceiq_custom_run_details", JSON.stringify(updatedDetails))

        setRuns([...updatedRuns, ...runs.filter(r => !updatedRuns.some(ur => ur.id === r.id))])
        setSelectedRunId(newRunItem.id)
      } catch (e) {
        console.error("Failed to save run to localStorage", e)
      }
    } catch (err: any) {
      setSimError(err.message || "Failed to trigger OpenAI simulation loop.")
    } finally {
      setSimulating(false)
    }
  }

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden font-sans pb-16">
      {/* Mesh Background effects */}
      <div className="absolute inset-0 w-full h-full pointer-events-none">
        <MeshGradient
          className="w-full h-full opacity-60"
          colors={["#000000", "#06b6d4", "#0891b2", "#164e63", "#f97316"]}
          speed={0.2}
        />
      </div>

      {/* Glassmorphic Header */}
      <header className="relative z-20 flex items-center justify-between px-8 py-6 backdrop-blur-md border-b border-white/5 bg-black/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center bg-cyan-500/20 border border-cyan-500/40">
            <span className="text-cyan-400 font-black text-lg">V</span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 via-white to-orange-400 bg-clip-text text-transparent">
              VoiceIQ Live Portal
            </h1>
            <p className="text-[10px] text-white/50 tracking-wider uppercase font-semibold">Testing Harness Dashboard</p>
          </div>
        </div>

        {/* Dynamic Navigation */}
        <nav className="flex space-x-1 p-1 bg-white/5 rounded-full border border-white/10">
          {(["calibration", "simulate", "history", "scenarios"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-1.5 rounded-full text-xs font-medium uppercase tracking-wider transition-all duration-300 ${
                activeTab === tab 
                  ? "bg-gradient-to-r from-cyan-500 to-orange-500 text-white shadow-lg" 
                  : "text-white/70 hover:text-white hover:bg-white/5"
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>

        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <div className="relative w-3 h-3">
            <span className="absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75 animate-ping"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
          </div>
          <span className="text-xs text-cyan-400 font-medium">LIVE DATABASE</span>
        </div>
      </header>

      {/* Main Panel */}
      <main className="relative z-10 max-w-7xl mx-auto px-8 mt-10">
        
        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-4">
            <div className="w-10 h-10 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin"></div>
            <p className="text-xs text-white/50">Fetching simulation logs from SQLite database...</p>
          </div>
        ) : (
          <AnimatePresence mode="wait">
            {activeTab === "calibration" && (
              <motion.div
                key="calibration"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-8"
              >
                {/* Left Columns - Metrics & List */}
                <div className="lg:col-span-2 space-y-8">
                  {/* Glassmorphic Metric Cards */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-lg">
                      <div className="text-[10px] text-white/40 uppercase tracking-widest font-semibold">Mean Absolute Error</div>
                      <div className="text-4xl font-black text-cyan-400 mt-2">{mae} <span className="text-xs font-normal text-white/50">pts</span></div>
                      <div className="text-[10px] text-white/30 mt-1">Average score deviation</div>
                    </div>
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-lg">
                      <div className="text-[10px] text-white/40 uppercase tracking-widest font-semibold">Systematic Bias</div>
                      <div className="text-4xl font-black text-orange-400 mt-2">
                        {parseFloat(bias) > 0 ? `+${bias}` : bias}
                      </div>
                      <div className="text-[10px] text-white/30 mt-1">Lenient (+) or Harsh (-)</div>
                    </div>
                    <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-lg">
                      <div className="text-[10px] text-white/40 uppercase tracking-widest font-semibold">Calibration Set Size</div>
                      <div className="text-4xl font-black text-white mt-2">{calibrationData.length} <span className="text-xs font-normal text-white/50">runs</span></div>
                      <div className="text-[10px] text-white/30 mt-1">Grades mapped</div>
                    </div>
                  </div>

                  {/* Calibration Table */}
                  <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md overflow-hidden">
                    <div className="px-6 py-4 border-b border-white/15 bg-white/5">
                      <h3 className="text-sm font-semibold tracking-wide">Judge vs Human Calibration Pairs (Click rows to inspect)</h3>
                    </div>
                    <div className="divide-y divide-white/5 max-h-[420px] overflow-y-auto">
                      {calibrationData.map((pair) => (
                        <button
                          key={pair.id}
                          onClick={() => setSelectedCalibId(pair.test_run_id)}
                          className={`w-full text-left px-6 py-4 flex items-center justify-between text-sm transition duration-150 hover:bg-white/5 focus:outline-none ${
                            selectedCalibId === pair.test_run_id ? "bg-white/10" : ""
                          }`}
                        >
                          <div>
                            <div className="font-medium">{pair.scenario_name}</div>
                            <div className="text-xs text-white/40">Run ID: #{pair.test_run_id}</div>
                          </div>
                          <div className="flex items-center gap-6">
                            <div className="text-right">
                              <span className="text-xs text-white/40 block">Human</span>
                              <span className="font-bold text-white">{pair.human_score}</span>
                            </div>
                            <div className="text-right">
                              <span className="text-xs text-white/40 block">Judge</span>
                              <span className="font-bold text-cyan-400">{pair.judge_score}</span>
                            </div>
                            <div className={`px-2 py-0.5 rounded text-xs font-semibold ${
                              Math.abs(pair.score_delta) > 5 ? "bg-red-500/20 text-red-400" : "bg-emerald-500/20 text-emerald-400"
                            }`}>
                              Δ {pair.score_delta > 0 ? `+${pair.score_delta.toFixed(1)}` : pair.score_delta.toFixed(1)}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Column - Dynamic Calibration Detail Inspection Panel */}
                <div className="lg:col-span-1 space-y-6">
                  {selectedCalibDetail ? (
                    <div className="p-6 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md space-y-6">
                      <h3 className="text-sm font-semibold tracking-wide border-b border-white/10 pb-3">Inspection: Run #{selectedCalibDetail.id}</h3>
                      
                      <div className="flex justify-between items-center bg-white/5 p-4 rounded-xl border border-white/10">
                        <div className="text-center">
                          <span className="text-[10px] text-white/50 uppercase block">Human Grade</span>
                          <span className="text-2xl font-black text-white">
                            {calibrationData.find(p => p.test_run_id === selectedCalibDetail.id)?.human_score || "N/A"}
                          </span>
                        </div>
                        <div className="h-8 w-px bg-white/10"></div>
                        <div className="text-center">
                          <span className="text-[10px] text-white/50 uppercase block">Judge Score</span>
                          <span className="text-2xl font-black text-cyan-400">{selectedCalibDetail.overall_score.toFixed(1)}</span>
                        </div>
                        <div className="h-8 w-px bg-white/10"></div>
                        <div className="text-center">
                          <span className="text-[10px] text-white/50 uppercase block">Difference</span>
                          <span className="text-2xl font-black text-orange-400">
                            {(() => {
                              const p = calibrationData.find(c => c.test_run_id === selectedCalibDetail.id)
                              return p ? (p.score_delta > 0 ? `+${p.score_delta.toFixed(0)}` : p.score_delta.toFixed(0)) : "0"
                            })()}
                          </span>
                        </div>
                      </div>

                      {/* Dimension comparisons */}
                      {selectedCalibDetail.scores_breakdown && (
                        <div>
                          <span className="text-xs font-semibold text-white/60 uppercase block mb-3">Scores Breakdown</span>
                          <div className="grid grid-cols-2 gap-3">
                            {Object.entries(selectedCalibDetail.scores_breakdown).map(([dim, val]) => (
                              <div key={dim} className="p-3 bg-white/5 rounded-xl border border-white/10">
                                <span className="text-[9px] text-white/40 uppercase block truncate">{dim.replace("_", " ")}</span>
                                <span className="text-sm font-bold text-white mt-1 block">{val}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Calibration notes */}
                      {calibrationData.find(p => p.test_run_id === selectedCalibDetail.id)?.notes && (
                        <div className="p-4 rounded-xl bg-orange-500/5 border border-orange-500/20 text-xs">
                          <strong className="text-orange-400 block mb-1">Human Notes & Justification:</strong>
                          <span className="text-white/70 italic leading-relaxed">
                            "{calibrationData.find(p => p.test_run_id === selectedCalibDetail.id)?.notes}"
                          </span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="h-64 flex flex-col items-center justify-center text-white/30 text-center p-6 border-2 border-dashed border-white/5 rounded-2xl">
                      <p className="text-xs">Click any calibration row to inspect the scoring breakdown, human comments, and difference statistics.</p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === "history" && (
              <motion.div
                key="history"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-8"
              >
                {/* Runs List */}
                <div className="lg:col-span-1 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md overflow-hidden flex flex-col h-[550px]">
                  <div className="px-6 py-4 border-b border-white/15 bg-white/5">
                    <h3 className="text-sm font-semibold tracking-wide">Select Test Run Logs</h3>
                  </div>
                  <div className="divide-y divide-white/5 overflow-y-auto flex-1">
                    {runs.map((run) => (
                      <button
                        key={run.id}
                        onClick={() => setSelectedRunId(run.id)}
                        className={`w-full text-left px-6 py-4 transition flex items-center justify-between hover:bg-white/5 ${
                          selectedRunId === run.id ? "bg-white/10" : ""
                        }`}
                      >
                        <div>
                          <div className="font-bold text-sm">{run.scenario_name}</div>
                          <div className="text-xs text-white/40 mt-1">Turns: {run.total_turns} · {run.difficulty_level}</div>
                        </div>
                        <div className="text-right">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                            run.overall_score >= 80 ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30" : 
                            run.overall_score >= 60 ? "bg-amber-500/15 text-amber-400 border border-amber-500/30" : 
                            "bg-red-500/15 text-red-400 border border-red-500/30"
                          }`}>
                            {run.overall_score.toFixed(0)}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Run Details Panel */}
                <div className="lg:col-span-2 space-y-6">
                  {runDetail ? (
                    <div className="p-6 rounded-2xl border border-white/10 bg-black/30 backdrop-blur-md space-y-6">
                      <div className="flex items-center justify-between pb-4 border-b border-white/10">
                        <div>
                          <h2 className="text-lg font-bold">{runDetail.scenario_name}</h2>
                          <p className="text-xs text-white/40">Difficulty: {runDetail.difficulty_level} · Status: {runDetail.goal_completed ? "✅ Goal achieved" : "❌ Hangup / Failure"}</p>
                        </div>
                        <div className="text-center">
                          <span className="text-[10px] text-white/40 uppercase tracking-widest block">Overall Score</span>
                          <span className="text-2xl font-black text-cyan-400">{runDetail.overall_score.toFixed(1)}</span>
                        </div>
                      </div>

                      {/* Score break-downs */}
                      {runDetail.scores_breakdown && (
                        <div className="grid grid-cols-5 gap-3">
                          {Object.entries(runDetail.scores_breakdown).map(([dim, val]) => (
                            <div key={dim} className="p-3 bg-white/5 rounded-xl border border-white/10 text-center">
                              <span className="text-[9px] text-white/50 uppercase block truncate">{dim.replace("_", " ")}</span>
                              <span className="text-lg font-bold text-white mt-1 block">{val}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Transcripts container */}
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-white/40 mb-3">Conversation Transcript</h3>
                        <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                          {runDetail.conversation_transcript && Array.isArray(runDetail.conversation_transcript) ? (
                            runDetail.conversation_transcript.map((turn, idx) => (
                              <div
                                key={idx}
                                className={`p-3 rounded-xl border text-sm leading-relaxed ${
                                  turn.role === "agent" 
                                    ? "bg-cyan-500/10 border-cyan-500/20 mr-12 text-cyan-50" 
                                    : "bg-orange-500/10 border-orange-500/20 ml-12 text-orange-50"
                                }`}
                              >
                                <span className={`text-[10px] font-bold uppercase block mb-1 ${
                                  turn.role === "agent" ? "text-cyan-400" : "text-orange-400"
                                }`}>
                                  {turn.role === "agent" ? "🤖 AI AGENT" : "📞 CUSTOMER SIMULATOR"}
                                </span>
                                {turn.content}
                              </div>
                            ))
                          ) : (
                            <p className="text-xs text-white/30">No transcripts parsed.</p>
                          )}
                        </div>
                      </div>

                      {/* Recommendations */}
                      {runDetail.recommendations && (
                        <div className="p-4 rounded-xl bg-orange-500/5 border border-orange-500/20">
                          <h4 className="text-xs font-bold text-orange-400 uppercase tracking-wider mb-2">📋 Judge Analysis & Recommendations</h4>
                          <p className="text-xs text-white/70 whitespace-pre-line leading-relaxed">{runDetail.recommendations}</p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="h-64 flex items-center justify-center text-white/30">Select a log history to view logs.</div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === "simulate" && (
              <motion.div
                key="simulate"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-1 lg:grid-cols-3 gap-8"
              >
                {/* Left controls column */}
                <div className="lg:col-span-1 p-6 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md space-y-6">
                  <h3 className="text-sm font-semibold tracking-wide border-b border-white/10 pb-3">Run Live Simulation</h3>
                  
                  {/* Select scenario input */}
                  <div>
                    <label className="text-xs text-white/50 block mb-2 font-medium">Select Caller Scenario</label>
                    <select
                      value={selectedScenarioId}
                      onChange={(e) => setSelectedScenarioId(parseInt(e.target.value))}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-500/50"
                    >
                      {scenarios.map((scen) => (
                        <option key={scen.id} value={scen.id} className="bg-black text-white">
                          {scen.scenario_name} ({scen.difficulty_level})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* System prompt input */}
                  <div>
                    <label className="text-xs text-white/50 block mb-2 font-medium">Agent System Prompt</label>
                    <textarea
                      value={agentPrompt}
                      onChange={(e) => setAgentPrompt(e.target.value)}
                      rows={8}
                      className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-xs text-white focus:outline-none focus:border-cyan-500/50 font-mono leading-relaxed"
                    />
                  </div>

                  {/* Run Button */}
                  <button
                    onClick={triggerSimulation}
                    disabled={simulating}
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-orange-500 text-white font-bold text-xs uppercase tracking-widest transition duration-300 disabled:opacity-50 hover:shadow-lg flex items-center justify-center gap-2"
                  >
                    {simulating ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                        <span>Simulating turns...</span>
                      </>
                    ) : (
                      <span>▶ Run Simulation</span>
                    )}
                  </button>

                  {simError && (
                    <div className="p-4 rounded-xl bg-red-500/15 border border-red-500/30 text-xs text-red-400">
                      <strong>Error:</strong> {simError}
                    </div>
                  )}
                </div>

                {/* Right transcript/results output column */}
                <div className="lg:col-span-2 space-y-6">
                  {simulating && (
                    <div className="p-8 rounded-2xl border border-white/10 bg-black/30 backdrop-blur-md flex flex-col items-center justify-center gap-4 text-center h-[450px]">
                      <div className="relative w-12 h-12 flex items-center justify-center">
                        <PulsingBorder
                          colors={["#06b6d4", "#f97316"]}
                          colorBack="#00000000"
                          speed={1.5}
                          roundness={1}
                          thickness={0.1}
                          intensity={4}
                          spots={4}
                          style={{ width: "40px", height: "40px" }}
                        />
                      </div>
                      <div>
                        <h4 className="font-bold text-sm">Simulation Loop Active</h4>
                        <p className="text-xs text-white/50 mt-1 max-w-sm">
                          Agent and customer simulator are exchanging messages in a turn-based loop using OpenAI gpt-4o-mini.
                          The LLM Judge will then run a consistency quality evaluation.
                        </p>
                      </div>
                    </div>
                  )}

                  {!simulating && simResult && (
                    <div className="p-6 rounded-2xl border border-white/10 bg-black/30 backdrop-blur-md space-y-6">
                      <div className="flex items-center justify-between pb-4 border-b border-white/10">
                        <div>
                          <h2 className="text-lg font-bold">Simulation Result</h2>
                          <p className="text-xs text-white/40">
                            Completed {simResult.total_turns} turns · Status: {simResult.goal_completed ? "✅ Goal achieved" : "❌ Caller Hungup"}
                          </p>
                        </div>
                        <div className="text-center">
                          <span className="text-[10px] text-white/40 uppercase tracking-widest block">Judge Score</span>
                          <span className="text-2xl font-black text-cyan-400">{simResult.overall_score.toFixed(1)}</span>
                        </div>
                      </div>

                      {/* Dimension breakdown */}
                      <div className="grid grid-cols-5 gap-3">
                        {Object.entries(simResult.scores_breakdown).map(([dim, val]: [string, any]) => (
                          <div key={dim} className="p-3 bg-white/5 rounded-xl border border-white/10 text-center">
                            <span className="text-[9px] text-white/50 uppercase block truncate">{dim.replace("_", " ")}</span>
                            <span className="text-lg font-bold text-white mt-1 block">{val}</span>
                          </div>
                        ))}
                      </div>

                      {/* Live transcript log */}
                      <div>
                        <h3 className="text-xs font-bold uppercase tracking-wider text-white/40 mb-3">Simulated Transcript</h3>
                        <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                          {simResult.transcript.map((turn: any, idx: number) => (
                            <div
                              key={idx}
                              className={`p-3 rounded-xl border text-sm leading-relaxed ${
                                turn.role === "agent" 
                                  ? "bg-cyan-500/10 border-cyan-500/20 mr-12 text-cyan-50" 
                                  : "bg-orange-500/10 border-orange-500/20 ml-12 text-orange-50"
                              }`}
                            >
                              <span className={`text-[10px] font-bold uppercase block mb-1 ${
                                turn.role === "agent" ? "text-cyan-400" : "text-orange-400"
                              }`}>
                                {turn.role === "agent" ? "🤖 AI AGENT" : "📞 CUSTOMER SIMULATOR"}
                              </span>
                              {turn.content}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Judge Failure Points */}
                      {simResult.failure_points && simResult.failure_points.length > 0 && (
                        <div>
                          <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider mb-2">⚠️ Detected Failure Points</h4>
                          <div className="space-y-2">
                            {simResult.failure_points.map((fp: any, idx: number) => (
                              <div key={idx} className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300">
                                <strong>Turn {fp.turn}:</strong> {fp.reason}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Recommendations */}
                      {simResult.recommendations && simResult.recommendations.length > 0 && (
                        <div className="p-4 rounded-xl bg-orange-500/5 border border-orange-500/20">
                          <h4 className="text-xs font-bold text-orange-400 uppercase tracking-wider mb-2">📋 Actionable Recommendations</h4>
                          <ul className="list-disc list-inside text-xs text-white/70 space-y-1">
                            {simResult.recommendations.map((rec: string, idx: number) => (
                              <li key={idx}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {!simulating && !simResult && (
                    <div className="h-[450px] border-2 border-dashed border-white/5 rounded-2xl flex flex-col items-center justify-center text-white/30 text-center p-8">
                      <svg className="w-12 h-12 text-white/10 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <h4 className="font-bold text-sm text-white/50">Ready to simulate</h4>
                      <p className="text-xs text-white/40 mt-1 max-w-xs">
                        Configure the agent system prompt on the left pane and trigger the simulation to watch it play out in real time.
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {activeTab === "scenarios" && (
              <motion.div
                key="scenarios"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              >
                {scenarios.map((scen) => (
                  <button
                    key={scen.id}
                    onClick={() => {
                      setSelectedScenarioId(scen.id)
                      setActiveTab("simulate")
                    }}
                    className="p-6 text-left rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md relative overflow-hidden group hover:border-cyan-500/40 hover:bg-white/5 transition duration-300 flex flex-col justify-between h-[220px] focus:outline-none w-full cursor-pointer"
                  >
                    <div className="w-full">
                      <div className="flex items-center justify-between mb-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          scen.difficulty_level === "easy" ? "bg-emerald-500/20 text-emerald-400" :
                          scen.difficulty_level === "medium" ? "bg-amber-500/20 text-amber-400" :
                          "bg-red-500/20 text-red-400"
                        }`}>
                          {scen.difficulty_level}
                        </span>
                        <span className="text-[10px] text-white/40 uppercase tracking-widest">{scen.caller_personality}</span>
                      </div>
                      <h4 className="font-bold text-base text-white group-hover:text-cyan-400 transition flex items-center justify-between">
                        <span>{scen.scenario_name}</span>
                        <span className="text-[10px] text-cyan-400 opacity-0 group-hover:opacity-100 transition-all duration-300 font-normal uppercase tracking-wider">
                          Run ⚡
                        </span>
                      </h4>
                      <p className="text-xs text-white/50 mt-2 line-clamp-3 leading-relaxed">{scen.scenario_description}</p>
                    </div>
                    <div className="pt-4 border-t border-white/5 mt-auto w-full">
                      <span className="text-[10px] text-white/30 uppercase tracking-widest block">Goal Condition</span>
                      <span className="text-xs text-white/80 block truncate mt-1">{scen.caller_goal}</span>
                    </div>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </main>
    </div>
  )
}

"use client"

import { useState } from "react"
import type { RetellAgentSummary } from "@/lib/types"

interface RetellPanelProps {
  agentPrompt: string
  onImportPrompt: (prompt: string, agentName?: string) => void
}

export function RetellPanel({ agentPrompt, onImportPrompt }: RetellPanelProps) {
  const [apiKey, setApiKey] = useState("")
  const [agents, setAgents] = useState<RetellAgentSummary[]>([])
  const [calls, setCalls] = useState<
    Array<{ call_id: string; agent_name?: string; call_status?: string }>
  >([])
  const [selectedAgent, setSelectedAgent] = useState("")
  const [loadingAgents, setLoadingAgents] = useState(false)
  const [loadingCalls, setLoadingCalls] = useState(false)
  const [importing, setImporting] = useState(false)
  const [judging, setJudging] = useState<string | null>(null)
  const [evaluation, setEvaluation] = useState<{
    overall_score: number
    failure_points: Array<{ turn: number; reason: string }>
    recommendations: string[]
  } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [importedName, setImportedName] = useState<string | null>(null)

  const headers = () => ({
    "Content-Type": "application/json",
    "x-retell-api-key": apiKey,
  })

  const loadAgents = async () => {
    if (!apiKey) {
      setError("Paste your Retell API key first.")
      return
    }
    setLoadingAgents(true)
    setError(null)
    try {
      const res = await fetch("/api/retell/agents", { headers: headers() })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)
      setAgents(data.agents)
      if (data.agents[0]) setSelectedAgent(data.agents[0].agent_id)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load agents.")
    } finally {
      setLoadingAgents(false)
    }
  }

  const importAgent = async () => {
    if (!selectedAgent) return
    setImporting(true)
    setError(null)
    try {
      const res = await fetch("/api/retell/agents", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ agent_id: selectedAgent }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)
      onImportPrompt(data.prompt, data.agent_name)
      setImportedName(data.agent_name)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to import agent.")
    } finally {
      setImporting(false)
    }
  }

  const loadCalls = async () => {
    if (!apiKey) {
      setError("Paste your Retell API key first.")
      return
    }
    setLoadingCalls(true)
    setError(null)
    try {
      const res = await fetch("/api/retell/calls", { headers: headers() })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)
      setCalls(data.calls)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load calls.")
    } finally {
      setLoadingCalls(false)
    }
  }

  const judgeCall = async (callId: string) => {
    setJudging(callId)
    setError(null)
    setEvaluation(null)
    try {
      const res = await fetch("/api/retell/calls", {
        method: "POST",
        headers: headers(),
        body: JSON.stringify({ call_id: callId }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail)
      setEvaluation({
        overall_score: data.evaluation.overall_score,
        failure_points: data.evaluation.failure_points,
        recommendations: data.evaluation.recommendations,
      })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to judge call.")
    } finally {
      setJudging(null)
    }
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
      <div className="space-y-5 rounded-2xl border border-white/10 bg-black/40 p-6 backdrop-blur-md">
        <h3 className="border-b border-white/10 pb-3 text-sm font-semibold">
          Retell agent import
        </h3>
        <p className="text-xs leading-relaxed text-white/50">
          Pull a live Retell LLM prompt into VoiceIQ for pre-launch scenario testing.
          API key stays in your browser session only — never stored server-side.
        </p>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Retell API key"
          className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-xs text-white focus:border-cyan-500/50 focus:outline-none"
        />
        <div className="flex flex-wrap gap-2">
          <button
            onClick={loadAgents}
            disabled={loadingAgents}
            className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-wider hover:bg-white/10 disabled:opacity-50"
          >
            {loadingAgents ? "Loading…" : "List agents"}
          </button>
          {agents.length > 0 && (
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="rounded-lg border border-white/10 bg-black px-3 py-2 text-xs text-white"
            >
              {agents.map((agent) => (
                <option key={agent.agent_id} value={agent.agent_id}>
                  {agent.agent_name} ({agent.response_engine_type || "agent"})
                </option>
              ))}
            </select>
          )}
          <button
            onClick={importAgent}
            disabled={!selectedAgent || importing}
            className="rounded-lg bg-cyan-500/20 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cyan-300 hover:bg-cyan-500/30 disabled:opacity-50"
          >
            {importing ? "Importing…" : "Import prompt"}
          </button>
        </div>
        {importedName && (
          <p className="text-xs text-emerald-400">
            Imported prompt from {importedName} — ready for Simulate or Batch tabs.
          </p>
        )}
        <div className="rounded-xl border border-white/5 bg-white/5 p-3">
          <p className="text-[10px] uppercase tracking-widest text-white/40">
            Current agent prompt preview
          </p>
          <p className="mt-2 max-h-32 overflow-y-auto font-mono text-[10px] leading-relaxed text-white/60">
            {agentPrompt.slice(0, 400)}
            {agentPrompt.length > 400 ? "…" : ""}
          </p>
        </div>
      </div>

      <div className="space-y-5 rounded-2xl border border-white/10 bg-black/40 p-6 backdrop-blur-md">
        <h3 className="border-b border-white/10 pb-3 text-sm font-semibold">
          Judge production calls
        </h3>
        <p className="text-xs leading-relaxed text-white/50">
          Fetch recent Retell call transcripts and run the same LLM judge used in
          simulation. Pairs with Retell Assure for post-launch QA.
        </p>
        <button
          onClick={loadCalls}
          disabled={loadingCalls}
          className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-wider hover:bg-white/10 disabled:opacity-50"
        >
          {loadingCalls ? "Loading…" : "Load recent calls"}
        </button>
        <div className="max-h-48 space-y-2 overflow-y-auto">
          {calls.map((call) => (
            <div
              key={call.call_id}
              className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-3 py-2"
            >
              <div>
                <p className="font-mono text-[10px] text-cyan-300">{call.call_id}</p>
                <p className="text-[10px] text-white/40">
                  {call.agent_name || "Unknown agent"} · {call.call_status || "unknown"}
                </p>
              </div>
              <button
                onClick={() => judgeCall(call.call_id)}
                disabled={judging === call.call_id}
                className="text-[10px] font-bold uppercase tracking-wider text-orange-400 hover:text-orange-300 disabled:opacity-50"
              >
                {judging === call.call_id ? "Judging…" : "Judge"}
              </button>
            </div>
          ))}
        </div>
        {evaluation && (
          <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
            <p className="text-[10px] uppercase tracking-widest text-white/40">
              Production call score
            </p>
            <p className="text-3xl font-black text-cyan-400">
              {evaluation.overall_score.toFixed(1)}
            </p>
            {evaluation.failure_points.length > 0 && (
              <ul className="mt-3 space-y-1 text-xs text-red-300">
                {evaluation.failure_points.slice(0, 3).map((fp) => (
                  <li key={`${fp.turn}-${fp.reason}`}>
                    Turn {fp.turn}: {fp.reason}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="lg:col-span-2 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-300">
          {error}
        </div>
      )}
    </div>
  )
}

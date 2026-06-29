"use client"

import { useEffect, useState } from "react"
import type { RunDetail, TestRun } from "@/lib/types"
import { loadCustomRunDetails } from "@/lib/run-storage"

interface HistoryPanelProps {
  runs: TestRun[]
}

export function HistoryPanel({ runs }: HistoryPanelProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<RunDetail | null>(null)

  useEffect(() => {
    if (runs.length > 0 && selectedId === null) {
      setSelectedId(runs[0].id)
    }
  }, [runs, selectedId])

  useEffect(() => {
    if (selectedId === null) return
    const local = loadCustomRunDetails().find((r) => r.id === selectedId)
    if (local) {
      setDetail(local)
      return
    }
    fetch(`/api/runs/${selectedId}`)
      .then((r) => r.json())
      .then(setDetail)
      .catch(console.error)
  }, [selectedId])

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div className="flex max-h-[560px] flex-col overflow-hidden rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md">
        <div className="border-b border-white/10 bg-white/5 px-6 py-4">
          <h3 className="text-sm font-semibold">Past runs</h3>
        </div>
        <div className="flex-1 divide-y divide-white/5 overflow-y-auto">
          {runs.map((run) => (
            <button
              key={run.id}
              onClick={() => setSelectedId(run.id)}
              className={`flex w-full items-center justify-between px-6 py-4 text-left hover:bg-white/5 ${
                selectedId === run.id ? "bg-white/10" : ""
              }`}
            >
              <div>
                <p className="text-sm font-bold">{run.scenario_name}</p>
                <p className="text-xs text-white/40">
                  {run.total_turns} turns · {run.difficulty_level}
                </p>
              </div>
              <ScoreBadge score={run.overall_score} />
            </button>
          ))}
        </div>
      </div>

      <div className="lg:col-span-2">
        {detail ? (
          <div className="space-y-6 rounded-2xl border border-white/10 bg-black/30 p-6 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <h2 className="text-lg font-bold">{detail.scenario_name}</h2>
                <p className="text-xs text-white/40">
                  {detail.goal_completed ? "✅ Goal achieved" : "❌ Hangup / fail"}
                </p>
              </div>
              <ScoreBadge score={detail.overall_score} large />
            </div>

            {detail.scores_breakdown && (
              <div className="grid grid-cols-5 gap-3">
                {Object.entries(detail.scores_breakdown).map(([dim, val]) => (
                  <div
                    key={dim}
                    className="rounded-xl border border-white/10 bg-white/5 p-3 text-center"
                  >
                    <span className="block truncate text-[9px] uppercase text-white/50">
                      {dim.replace("_", " ")}
                    </span>
                    <span className="mt-1 block text-lg font-bold">{val}</span>
                  </div>
                ))}
              </div>
            )}

            <div>
              <h3 className="mb-3 text-xs font-bold uppercase text-white/40">
                Transcript
              </h3>
              <div className="max-h-64 space-y-3 overflow-y-auto">
                {detail.conversation_transcript?.map((turn, idx) => (
                  <div
                    key={idx}
                    className={`rounded-xl border p-3 text-sm ${
                      turn.role === "agent"
                        ? "mr-12 border-cyan-500/20 bg-cyan-500/10"
                        : "ml-12 border-orange-500/20 bg-orange-500/10"
                    }`}
                  >
                    {turn.content}
                  </div>
                ))}
              </div>
            </div>

            {detail.recommendations && (
              <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-4 text-xs text-white/70">
                {detail.recommendations}
              </div>
            )}
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center text-white/30">
            Select a run
          </div>
        )}
      </div>
    </div>
  )
}

function ScoreBadge({ score, large }: { score: number; large?: boolean }) {
  const className =
    score >= 80
      ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
      : score >= 60
        ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
        : "bg-red-500/15 text-red-400 border-red-500/30"
  return (
    <span
      className={`rounded-full border px-2.5 py-1 font-bold ${className} ${
        large ? "text-lg" : "text-xs"
      }`}
    >
      {score.toFixed(0)}
    </span>
  )
}

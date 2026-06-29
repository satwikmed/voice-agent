"use client"

import { useEffect, useState } from "react"
import type { CalibrationPair, RunDetail } from "@/lib/types"
import { loadCustomRunDetails } from "@/lib/run-storage"

interface CalibrationPanelProps {
  calibrationData: CalibrationPair[]
}

export function CalibrationPanel({ calibrationData }: CalibrationPanelProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<RunDetail | null>(null)

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

  useEffect(() => {
    if (calibrationData.length > 0 && selectedId === null) {
      setSelectedId(calibrationData[0].test_run_id)
    }
  }, [calibrationData, selectedId])

  const mae =
    calibrationData.length > 0
      ? (
          calibrationData.reduce(
            (acc, c) => acc + Math.abs(c.judge_score - c.human_score),
            0
          ) / calibrationData.length
        ).toFixed(1)
      : "N/A"

  const bias =
    calibrationData.length > 0
      ? (
          calibrationData.reduce((acc, c) => acc + (c.judge_score - c.human_score), 0) /
          calibrationData.length
        ).toFixed(1)
      : "N/A"

  const selectedPair = calibrationData.find((p) => p.test_run_id === selectedId)

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <div className="grid grid-cols-3 gap-4">
          <MetricCard label="Mean absolute error" value={`${mae} pts`} accent="cyan" />
          <MetricCard
            label="Systematic bias"
            value={parseFloat(bias) > 0 ? `+${bias}` : bias}
            accent="orange"
          />
          <MetricCard
            label="Calibration pairs"
            value={String(calibrationData.length)}
            accent="white"
          />
        </div>

        <div className="overflow-hidden rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md">
          <div className="border-b border-white/10 bg-white/5 px-6 py-4">
            <h3 className="text-sm font-semibold">Judge vs human grades</h3>
          </div>
          <div className="max-h-[420px] divide-y divide-white/5 overflow-y-auto">
            {calibrationData.map((pair) => (
              <button
                key={pair.id}
                onClick={() => setSelectedId(pair.test_run_id)}
                className={`flex w-full items-center justify-between px-6 py-4 text-left text-sm hover:bg-white/5 ${
                  selectedId === pair.test_run_id ? "bg-white/10" : ""
                }`}
              >
                <div>
                  <p className="font-medium">{pair.scenario_name}</p>
                  <p className="text-xs text-white/40">Run #{pair.test_run_id}</p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-white">{pair.human_score}</span>
                  <span className="text-cyan-400">{pair.judge_score}</span>
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      Math.abs(pair.score_delta) > 5
                        ? "bg-red-500/20 text-red-400"
                        : "bg-emerald-500/20 text-emerald-400"
                    }`}
                  >
                    Δ {pair.score_delta > 0 ? "+" : ""}
                    {pair.score_delta.toFixed(1)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-black/40 p-6 backdrop-blur-md">
        {selectedPair && detail ? (
          <div className="space-y-4">
            <h3 className="border-b border-white/10 pb-3 text-sm font-semibold">
              Run #{detail.id}
            </h3>
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div>
                <p className="text-[10px] text-white/40">Human</p>
                <p className="text-xl font-bold">{selectedPair.human_score}</p>
              </div>
              <div>
                <p className="text-[10px] text-white/40">Judge</p>
                <p className="text-xl font-bold text-cyan-400">
                  {detail.overall_score.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-[10px] text-white/40">Delta</p>
                <p className="text-xl font-bold text-orange-400">
                  {selectedPair.score_delta > 0 ? "+" : ""}
                  {selectedPair.score_delta.toFixed(0)}
                </p>
              </div>
            </div>
            {selectedPair.notes && (
              <p className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-3 text-xs italic text-white/70">
                {selectedPair.notes}
              </p>
            )}
          </div>
        ) : (
          <p className="text-center text-xs text-white/40">Select a row to inspect.</p>
        )}
      </div>
    </div>
  )
}

function MetricCard({
  label,
  value,
  accent,
}: {
  label: string
  value: string
  accent: "cyan" | "orange" | "white"
}) {
  const color =
    accent === "cyan"
      ? "text-cyan-400"
      : accent === "orange"
        ? "text-orange-400"
        : "text-white"
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-lg">
      <p className="text-[10px] uppercase tracking-widest text-white/40">{label}</p>
      <p className={`mt-2 text-3xl font-black ${color}`}>{value}</p>
    </div>
  )
}

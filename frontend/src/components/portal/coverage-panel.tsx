"use client"

import { buildCoverageMatrix, overallCoveragePercent } from "@/lib/coverage"
import type { CoverageCategory, Scenario, TestRun } from "@/lib/types"

interface CoveragePanelProps {
  categories: CoverageCategory[]
  scenarios: Scenario[]
  runs: TestRun[]
}

export function CoveragePanel({
  categories,
  scenarios,
  runs,
}: CoveragePanelProps) {
  const matrix = buildCoverageMatrix(categories, scenarios, runs)
  const overall = overallCoveragePercent(matrix)

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-lg">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-white/40">
            Overall coverage
          </p>
          <p className="mt-2 text-4xl font-black text-cyan-400">{overall}%</p>
          <p className="mt-1 text-[10px] text-white/30">
            Categories with at least one executed scenario
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-lg">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-white/40">
            Scenario library
          </p>
          <p className="mt-2 text-4xl font-black text-white">{scenarios.length}</p>
          <p className="mt-1 text-[10px] text-white/30">
            Including Retell vertical templates
          </p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-lg">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-white/40">
            Blind spots
          </p>
          <p className="mt-2 text-4xl font-black text-orange-400">
            {matrix.filter((c) => c.coveragePercent < 100).length}
          </p>
          <p className="mt-1 text-[10px] text-white/30">
            Coverage categories not fully tested
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {matrix.map((cell) => (
          <div
            key={cell.category.id}
            className="rounded-2xl border border-white/10 bg-black/40 p-5 backdrop-blur-md"
          >
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold">{cell.category.label}</h3>
                <p className="text-xs text-white/50">{cell.category.description}</p>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-bold ${
                  cell.coveragePercent === 100
                    ? "bg-emerald-500/15 text-emerald-400"
                    : cell.coveragePercent > 0
                      ? "bg-amber-500/15 text-amber-400"
                      : "bg-red-500/15 text-red-400"
                }`}
              >
                {cell.coveragePercent}%
              </span>
            </div>
            <div className="space-y-2">
              {cell.scenarios.length === 0 ? (
                <p className="text-xs text-white/30">No mapped scenarios yet.</p>
              ) : (
                cell.scenarios.map(({ scenario, tested, bestScore, runCount }) => (
                  <div
                    key={scenario.id}
                    className="flex items-center justify-between rounded-xl border border-white/5 bg-white/5 px-3 py-2"
                  >
                    <div>
                      <p className="text-xs font-medium">{scenario.scenario_name}</p>
                      <p className="text-[10px] text-white/40">
                        {scenario.difficulty_level} · {runCount} run
                        {runCount === 1 ? "" : "s"}
                      </p>
                    </div>
                    <div className="text-right">
                      {tested ? (
                        <span
                          className={`text-sm font-bold ${
                            (bestScore || 0) >= 70
                              ? "text-emerald-400"
                              : "text-red-400"
                          }`}
                        >
                          {bestScore?.toFixed(0)}
                        </span>
                      ) : (
                        <span className="text-[10px] uppercase tracking-wider text-red-400">
                          blind
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

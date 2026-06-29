import type { SimulationResult } from "@/lib/types"

interface SimulationResultViewProps {
  result: SimulationResult
  title?: string
}

export function SimulationResultView({
  result,
  title = "Simulation result",
}: SimulationResultViewProps) {
  return (
    <div className="space-y-6 rounded-2xl border border-white/10 bg-black/30 p-6 backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-white/10 pb-4">
        <div>
          <h2 className="text-lg font-bold">{title}</h2>
          <p className="text-xs text-white/40">
            {result.total_turns} turns ·{" "}
            {result.goal_completed ? "✅ Goal achieved" : "❌ Caller hung up"}
          </p>
        </div>
        <div className="text-center">
          <span className="block text-[10px] uppercase tracking-widest text-white/40">
            Judge score
          </span>
          <span className="text-2xl font-black text-cyan-400">
            {result.overall_score.toFixed(1)}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-3">
        {Object.entries(result.scores_breakdown).map(([dim, val]) => (
          <div
            key={dim}
            className="rounded-xl border border-white/10 bg-white/5 p-3 text-center"
          >
            <span className="block truncate text-[9px] uppercase text-white/50">
              {dim.replace("_", " ")}
            </span>
            <span className="mt-1 block text-lg font-bold text-white">{val}</span>
          </div>
        ))}
      </div>

      <div>
        <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-white/40">
          Transcript
        </h3>
        <div className="max-h-64 space-y-3 overflow-y-auto pr-2">
          {result.transcript.map((turn, idx) => (
            <div
              key={idx}
              className={`rounded-xl border p-3 text-sm leading-relaxed ${
                turn.role === "agent"
                  ? "mr-12 border-cyan-500/20 bg-cyan-500/10 text-cyan-50"
                  : "ml-12 border-orange-500/20 bg-orange-500/10 text-orange-50"
              }`}
            >
              <span
                className={`mb-1 block text-[10px] font-bold uppercase ${
                  turn.role === "agent" ? "text-cyan-400" : "text-orange-400"
                }`}
              >
                {turn.role === "agent" ? "🤖 Agent" : "📞 Caller"}
              </span>
              {turn.content}
            </div>
          ))}
        </div>
      </div>

      {result.failure_points.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-red-400">
            Failure points
          </h4>
          {result.failure_points.map((fp, idx) => (
            <div
              key={idx}
              className="rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-300"
            >
              <strong>Turn {fp.turn}:</strong> {fp.reason}
            </div>
          ))}
        </div>
      )}

      {result.recommendations.length > 0 && (
        <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-4">
          <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-orange-400">
            Recommendations
          </h4>
          <ul className="list-inside list-disc space-y-1 text-xs text-white/70">
            {result.recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

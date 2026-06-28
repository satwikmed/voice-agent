import type { DeployGateResult } from "@/lib/types"

interface DeployGateBannerProps {
  gate: DeployGateResult
}

export function DeployGateBanner({ gate }: DeployGateBannerProps) {
  return (
    <div
      className={`mb-8 rounded-2xl border p-5 backdrop-blur-md ${
        gate.passed
          ? "border-emerald-500/30 bg-emerald-500/10"
          : "border-red-500/30 bg-red-500/10"
      }`}
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/50">
            Pre-launch deploy gate
          </p>
          <h2 className="mt-1 text-xl font-black">
            {gate.passed ? "✅ Cleared to ship" : "🛑 Hold deployment"}
          </h2>
          <p className="mt-1 text-xs text-white/60">
            {gate.scenariosPassed}/{gate.scenariosTested} scenarios pass at 70+ · gate
            requires {Math.round(gate.threshold * 100)}% pass rate
            {gate.weakestScenario ? ` · weakest: ${gate.weakestScenario}` : ""}
          </p>
        </div>
        <div className="text-right">
          <div
            className={`text-4xl font-black ${
              gate.passed ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {Math.round(gate.passRate * 100)}%
          </div>
          <p className="text-[10px] uppercase tracking-widest text-white/40">
            suite pass rate
          </p>
        </div>
      </div>
      {!gate.passed && gate.blockers.length > 0 && (
        <ul className="mt-4 space-y-1 border-t border-white/10 pt-4 text-xs text-red-200/90">
          {gate.blockers.map((blocker) => (
            <li key={blocker}>• {blocker}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

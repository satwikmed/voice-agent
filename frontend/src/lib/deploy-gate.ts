import type { DeployGateResult, Scenario, TestRun } from "./types"

export const DEPLOY_PASS_THRESHOLD = 70
export const DEPLOY_GATE_THRESHOLD = 0.9

export function evaluateDeployGate(
  scenarios: Scenario[],
  runs: TestRun[],
  batchResults?: Array<{ scenario_id: number; overall_score: number }>
): DeployGateResult {
  const blockers: string[] = []
  const source =
    batchResults && batchResults.length > 0
      ? batchResults
      : scenarios.map((scenario) => {
          const scenarioRuns = runs.filter((r) => r.scenario_id === scenario.id)
          const best =
            scenarioRuns.length > 0
              ? Math.max(...scenarioRuns.map((r) => r.overall_score))
              : 0
          return { scenario_id: scenario.id, overall_score: best }
        })

  const tested = source.filter((r) => r.overall_score > 0)
  const passed = tested.filter((r) => r.overall_score >= DEPLOY_PASS_THRESHOLD)

  if (tested.length < scenarios.length) {
    const missing = scenarios.length - tested.length
    blockers.push(`${missing} scenario(s) never tested`)
  }

  const hardFailures = tested.filter((r) => {
    const scenario = scenarios.find((s) => s.id === r.scenario_id)
    return (
      scenario?.difficulty_level === "hard" &&
      r.overall_score < DEPLOY_PASS_THRESHOLD
    )
  })

  hardFailures.forEach((r) => {
    const scenario = scenarios.find((s) => s.id === r.scenario_id)
    if (scenario) {
      blockers.push(
        `Hard scenario "${scenario.scenario_name}" scored ${r.overall_score.toFixed(0)} (need ${DEPLOY_PASS_THRESHOLD}+)`
      )
    }
  })

  const passRate = tested.length === 0 ? 0 : passed.length / tested.length
  const weakest = [...tested].sort((a, b) => a.overall_score - b.overall_score)[0]
  const weakestScenario = weakest
    ? scenarios.find((s) => s.id === weakest.scenario_id)?.scenario_name
    : undefined

  if (passRate < DEPLOY_GATE_THRESHOLD) {
    blockers.push(
      `Pass rate ${Math.round(passRate * 100)}% below ${Math.round(DEPLOY_GATE_THRESHOLD * 100)}% gate`
    )
  }

  return {
    passRate,
    threshold: DEPLOY_GATE_THRESHOLD,
    passed: blockers.length === 0 && tested.length === scenarios.length,
    scenariosTested: tested.length,
    scenariosPassed: passed.length,
    blockers,
    weakestScenario,
  }
}

import type { CoverageCategory, Scenario, TestRun } from "./types"

export interface CoverageCell {
  category: CoverageCategory
  scenarios: Array<{
    scenario: Scenario
    tested: boolean
    bestScore: number | null
    runCount: number
  }>
  coveragePercent: number
}

export function buildCoverageMatrix(
  categories: CoverageCategory[],
  scenarios: Scenario[],
  runs: TestRun[]
): CoverageCell[] {
  return categories.map((category) => {
    const tagged = scenarios.filter((s) =>
      (s.coverage_tags || []).includes(category.id)
    )

    const scenariosInCell = tagged.map((scenario) => {
      const scenarioRuns = runs.filter((r) => r.scenario_id === scenario.id)
      const bestScore =
        scenarioRuns.length > 0
          ? Math.max(...scenarioRuns.map((r) => r.overall_score))
          : null

      return {
        scenario,
        tested: scenarioRuns.length > 0,
        bestScore,
        runCount: scenarioRuns.length,
      }
    })

    const testedCount = scenariosInCell.filter((s) => s.tested).length
    const coveragePercent =
      scenariosInCell.length === 0
        ? 0
        : Math.round((testedCount / scenariosInCell.length) * 100)

    return {
      category,
      scenarios: scenariosInCell,
      coveragePercent,
    }
  })
}

export function overallCoveragePercent(cells: CoverageCell[]): number {
  const withScenarios = cells.filter((c) => c.scenarios.length > 0)
  if (withScenarios.length === 0) return 0
  const total = withScenarios.reduce((acc, c) => acc + c.coveragePercent, 0)
  return Math.round(total / withScenarios.length)
}

import type { RunDetail, TestRun } from "./types"

export function loadCustomRuns(): TestRun[] {
  try {
    const stored = localStorage.getItem("voiceiq_custom_runs")
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

export function loadCustomRunDetails(): RunDetail[] {
  try {
    const stored = localStorage.getItem("voiceiq_custom_run_details")
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

export function saveCustomRun(run: TestRun, detail: RunDetail) {
  const runs = [run, ...loadCustomRuns().filter((r) => r.id !== run.id)]
  const details = [detail, ...loadCustomRunDetails().filter((r) => r.id !== detail.id)]
  localStorage.setItem("voiceiq_custom_runs", JSON.stringify(runs))
  localStorage.setItem("voiceiq_custom_run_details", JSON.stringify(details))
  return { runs, details }
}

export interface SuiteResultSummary {
  scenario_id: number
  scenario_name: string
  difficulty_level: string
  overall_score: number
  goal_completed: boolean
  total_turns: number
}

export function saveSuiteResults(
  results: Array<
    SuiteResultSummary & {
      transcript: RunDetail["conversation_transcript"]
      scores_breakdown: RunDetail["scores_breakdown"]
      failure_points: RunDetail["failure_points"]
      recommendations: string[]
    }
  >,
  agentPrompt: string
): TestRun[] {
  const baseId = Date.now()
  const newRuns: TestRun[] = []
  const newDetails: RunDetail[] = []

  results.forEach((r, idx) => {
    const id = baseId + idx
    newRuns.push({
      id,
      scenario_id: r.scenario_id,
      scenario_name: r.scenario_name,
      difficulty_level: r.difficulty_level,
      overall_score: r.overall_score,
      total_turns: r.total_turns,
      goal_completed: r.goal_completed ? 1 : 0,
      created_at: new Date().toISOString(),
      source: "batch",
    })
    newDetails.push({
      id,
      scenario_id: r.scenario_id,
      scenario_name: r.scenario_name,
      difficulty_level: r.difficulty_level,
      overall_score: r.overall_score,
      total_turns: r.total_turns,
      goal_completed: r.goal_completed ? 1 : 0,
      created_at: new Date().toISOString(),
      agent_system_prompt: agentPrompt,
      conversation_transcript: r.transcript,
      scores_breakdown: r.scores_breakdown,
      failure_points: r.failure_points,
      recommendations: r.recommendations.join("\n"),
      source: "batch",
    })
  })

  const allRuns = [...newRuns, ...loadCustomRuns()]
  const allDetails = [...newDetails, ...loadCustomRunDetails()]
  localStorage.setItem("voiceiq_custom_runs", JSON.stringify(allRuns))
  localStorage.setItem("voiceiq_custom_run_details", JSON.stringify(allDetails))
  return allRuns
}

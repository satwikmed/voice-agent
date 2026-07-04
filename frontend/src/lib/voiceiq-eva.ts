import type { FailurePoint, ScoresBreakdown, TranscriptTurn } from "./types"

export type EvaDomain =
  | "airline_csm"
  | "healthcare_hrsd"
  | "enterprise_itsm"

export interface EvaScenario {
  eva_id: string
  domain: EvaDomain
  domain_label: string
  scenario_name: string
  scenario_description: string
  caller_personality: string
  caller_goal: string
  difficulty_level: string
  hangup_triggers?: string[]
  behavior_rules?: string[]
  persona_prompt: string
  must_have_criteria: string[]
  starting_utterance: string
  tool_density: "low" | "medium" | "high"
  agent_context?: string
}

export interface EvaScores {
  eva_a: number
  eva_x: number
  eva_a_pass: boolean
  eva_x_pass: boolean
  composite_pass: boolean
  eva_a_breakdown: {
    task_completion: number
    goal_achieved_signal: number
    faithfulness_proxy: number
  }
  eva_x_breakdown: {
    conversation_progression: number
    spoken_conciseness_proxy: number
    empathy: number
    turn_taking_proxy: number
  }
}

export interface EvaRunResult {
  eva_id: string
  domain: EvaDomain
  domain_label: string
  scenario_name: string
  goal_completed: boolean
  total_turns: number
  overall_score: number
  eva_a: number
  eva_x: number
  eva_a_pass: boolean
  eva_x_pass: boolean
  composite_pass: boolean
  scores_breakdown: ScoresBreakdown
  failure_points: FailurePoint[]
  recommendations: string[]
  transcript?: TranscriptTurn[]
}

export interface EvaBenchmarkSummary {
  scenario_count: number
  eva_a_pass_at_1: number
  eva_x_pass_at_1: number
  composite_pass_at_1: number
  avg_eva_a: number
  avg_eva_x: number
  by_domain: Record<
    string,
    {
      scenario_count: number
      eva_a_pass_at_1: number
      eva_x_pass_at_1: number
      composite_pass_at_1: number
      avg_eva_a: number
      avg_eva_x: number
    }
  >
}

export const EVA_A_PASS = 0.7
export const EVA_X_PASS = 0.7
export const EVA_COMPOSITE_GATE = 0.6

export const DOMAIN_AGENT_PROMPTS: Record<EvaDomain, string> = {
  airline_csm: `You are a Retell AI voice agent for SkyBridge Airlines customer service.

RULES FOR PHONE CONVERSATIONS:
- Speak in short, natural sentences. No markdown, bullets, or URLs.
- Use ONLY facts from the BACKEND STATE section below.
- Authenticate the caller before changing bookings.
- State total out-of-pocket cost before confirming any change.
- Assign and confirm seat, flight, date, arrival time, and confirmation code.

Be professional, concise, and empathetic.`,
  healthcare_hrsd: `You are a Retell AI voice agent for Meridian Health System HR Service Desk.

RULES FOR PHONE CONVERSATIONS:
- Use ONLY facts from the BACKEND STATE section below.
- Verify caller identity (NPI + PIN, or employee ID + DOB) before accessing records.
- When credentials match BACKEND STATE, accept verification immediately.
- Follow the RESOLUTION SCRIPT step-by-step once verified.
- Repeat case IDs digit-by-digit. Never invent identifiers.

Be calm and precise.`,
  enterprise_itsm: `You are a Retell AI voice agent for NovaCorp IT Service Desk.

RULES FOR PHONE CONVERSATIONS:
- Use ONLY facts from the BACKEND STATE section below.
- Authenticate employee (employee ID + phone last four) before account changes.
- When credentials match BACKEND STATE, proceed immediately.
- Follow the RESOLUTION SCRIPT step-by-step for the caller's issue.

Be efficient and clear.`,
}

export function buildEvaAgentPrompt(
  scenario: EvaScenario,
  customPrompt?: string
): string {
  const base =
    customPrompt?.trim() ||
    DOMAIN_AGENT_PROMPTS[scenario.domain] ||
    DOMAIN_AGENT_PROMPTS.airline_csm
  const context = scenario.agent_context?.trim()
  if (!context) return base
  return `${base}\n\n---\n${context}\n---`
}

export function scoreEvaRun(
  goalCompleted: boolean,
  judgeScores: ScoresBreakdown
): EvaScores {
  const goalCompletion = judgeScores.goal_completion / 100
  const responseRelevance = judgeScores.response_relevance / 100
  const conversationFlow = judgeScores.conversation_flow / 100
  const empathy = judgeScores.empathy / 100
  const objectionHandling = judgeScores.objection_handling / 100
  const goalSignal = goalCompleted ? 1 : 0

  const eva_a =
    goalCompletion * 0.45 + goalSignal * 0.35 + responseRelevance * 0.2
  const eva_x =
    conversationFlow * 0.4 +
    responseRelevance * 0.3 +
    empathy * 0.2 +
    objectionHandling * 0.1

  const eva_a_pass = eva_a >= EVA_A_PASS
  const eva_x_pass = eva_x >= EVA_X_PASS

  return {
    eva_a: Math.round(eva_a * 1000) / 1000,
    eva_x: Math.round(eva_x * 1000) / 1000,
    eva_a_pass,
    eva_x_pass,
    composite_pass: eva_a_pass && eva_x_pass,
    eva_a_breakdown: {
      task_completion: goalCompletion,
      goal_achieved_signal: goalSignal,
      faithfulness_proxy: responseRelevance,
    },
    eva_x_breakdown: {
      conversation_progression: conversationFlow,
      spoken_conciseness_proxy: responseRelevance,
      empathy,
      turn_taking_proxy: objectionHandling,
    },
  }
}

export function aggregateEvaBenchmark(
  runs: EvaRunResult[]
): EvaBenchmarkSummary {
  if (runs.length === 0) {
    return {
      scenario_count: 0,
      eva_a_pass_at_1: 0,
      eva_x_pass_at_1: 0,
      composite_pass_at_1: 0,
      avg_eva_a: 0,
      avg_eva_x: 0,
      by_domain: {},
    }
  }

  const passRate = (items: EvaRunResult[], key: "eva_a_pass" | "eva_x_pass" | "composite_pass") =>
    items.filter((item) => item[key]).length / items.length

  const byDomain: EvaBenchmarkSummary["by_domain"] = {}
  const domains = [...new Set(runs.map((r) => r.domain))]

  for (const domain of domains) {
    const items = runs.filter((r) => r.domain === domain)
    byDomain[domain] = {
      scenario_count: items.length,
      eva_a_pass_at_1: passRate(items, "eva_a_pass"),
      eva_x_pass_at_1: passRate(items, "eva_x_pass"),
      composite_pass_at_1: passRate(items, "composite_pass"),
      avg_eva_a: items.reduce((s, r) => s + r.eva_a, 0) / items.length,
      avg_eva_x: items.reduce((s, r) => s + r.eva_x, 0) / items.length,
    }
  }

  return {
    scenario_count: runs.length,
    eva_a_pass_at_1: passRate(runs, "eva_a_pass"),
    eva_x_pass_at_1: passRate(runs, "eva_x_pass"),
    composite_pass_at_1: passRate(runs, "composite_pass"),
    avg_eva_a: runs.reduce((s, r) => s + r.eva_a, 0) / runs.length,
    avg_eva_x: runs.reduce((s, r) => s + r.eva_x, 0) / runs.length,
    by_domain: byDomain,
  }
}

export function evaluateEvaDeployGate(summary: EvaBenchmarkSummary): {
  passed: boolean
  blockers: string[]
} {
  const blockers: string[] = []

  if (summary.composite_pass_at_1 < EVA_COMPOSITE_GATE) {
    blockers.push(
      `Composite pass@1 ${Math.round(summary.composite_pass_at_1 * 100)}% below ${Math.round(EVA_COMPOSITE_GATE * 100)}% gate`
    )
  }

  for (const [domain, stats] of Object.entries(summary.by_domain)) {
    if (stats.composite_pass_at_1 < EVA_COMPOSITE_GATE) {
      blockers.push(
        `${domain}: composite pass@1 ${Math.round(stats.composite_pass_at_1 * 100)}% (need ${Math.round(EVA_COMPOSITE_GATE * 100)}%+)`
      )
    }
  }

  return { passed: blockers.length === 0, blockers }
}

export interface Scenario {
  id: number
  scenario_name: string
  scenario_description: string
  caller_personality: string
  caller_goal: string
  difficulty_level: string
  hangup_triggers?: string[]
  behavior_rules?: string[]
  persona_prompt: string
  vertical?: string
  coverage_tags?: string[]
}

export interface TranscriptTurn {
  turn: number
  role: "agent" | "caller"
  content: string
}

export interface ScoresBreakdown {
  response_relevance: number
  objection_handling: number
  conversation_flow: number
  empathy: number
  goal_completion: number
}

export interface FailurePoint {
  turn: number
  reason: string
}

export interface SimulationResult {
  run_id: number
  transcript: TranscriptTurn[]
  total_turns: number
  goal_completed: boolean
  overall_score: number
  scores_breakdown: ScoresBreakdown
  failure_points: FailurePoint[]
  recommendations: string[]
}

export interface TestRun {
  id: number
  scenario_id: number
  scenario_name: string
  difficulty_level: string
  overall_score: number
  total_turns: number
  goal_completed: number
  created_at: string
  source?: "seed" | "simulation" | "retell" | "batch"
}

export interface RunDetail extends TestRun {
  agent_system_prompt: string
  conversation_transcript: TranscriptTurn[]
  scores_breakdown: ScoresBreakdown
  failure_points: FailurePoint[]
  recommendations: string
}

export interface CalibrationPair {
  id: number
  test_run_id: number
  human_score: number
  judge_score: number
  score_delta: number
  notes: string
  scenario_name: string
}

export interface CoverageCategory {
  id: string
  label: string
  description: string
}

export interface DeployGateResult {
  passRate: number
  threshold: number
  passed: boolean
  scenariosTested: number
  scenariosPassed: number
  blockers: string[]
  weakestScenario?: string
}

export interface RetellAgentSummary {
  agent_id: string
  agent_name: string
  version?: number
  response_engine_type?: string
}

export interface RetellCallSummary {
  call_id: string
  agent_id?: string
  agent_name?: string
  start_timestamp?: number
  duration_ms?: number
  call_status?: string
  overall_score?: number
}

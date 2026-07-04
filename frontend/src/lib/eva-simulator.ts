import {
  buildCallerSystemPrompt,
  callOpenAI,
  formatTranscriptForJudge,
  JUDGE_SYSTEM_PROMPT,
  MAX_TURNS,
  parseJudgeResponse,
} from "./judge"
import {
  buildEvaAgentPrompt,
  scoreEvaRun,
  type EvaRunResult,
  type EvaScenario,
} from "./voiceiq-eva"
import type { TranscriptTurn } from "./types"

export async function runEvaSimulation(
  apiKey: string,
  scenario: EvaScenario,
  customAgentPrompt?: string
): Promise<EvaRunResult> {
  const agentPrompt = buildEvaAgentPrompt(scenario, customAgentPrompt)
  const callerSystemPrompt = buildCallerSystemPrompt(scenario.persona_prompt)

  const agentMessages: Array<{ role: string; content: string }> = [
    { role: "system", content: agentPrompt },
  ]
  const callerMessages: Array<{ role: string; content: string }> = [
    { role: "system", content: callerSystemPrompt },
  ]

  const transcript: TranscriptTurn[] = []
  let goalCompleted = false
  let totalTurns = 0

  for (let turn = 1; turn <= MAX_TURNS; turn++) {
    totalTurns = turn

    const agentText = await callOpenAI(apiKey, agentMessages, {
      temperature: 0.3,
    })
    transcript.push({ turn, role: "agent", content: agentText })
    agentMessages.push({ role: "assistant", content: agentText })
    callerMessages.push({ role: "user", content: agentText })

    let callerText: string
    if (turn === 1 && scenario.starting_utterance?.trim()) {
      callerText = scenario.starting_utterance.trim()
    } else {
      callerText = await callOpenAI(apiKey, callerMessages, {
        temperature: 0.7,
      })
    }

    transcript.push({ turn, role: "caller", content: callerText })
    callerMessages.push({ role: "assistant", content: callerText })
    agentMessages.push({ role: "user", content: callerText })

    if (callerText.includes("[GOAL_ACHIEVED]")) {
      goalCompleted = true
      break
    }
    if (callerText.includes("[HANGUP]")) break
  }

  const judgePrompt = formatTranscriptForJudge(
    scenario.scenario_description,
    transcript
  )
  const judgeRaw = await callOpenAI(
    apiKey,
    [
      { role: "system", content: JUDGE_SYSTEM_PROMPT },
      { role: "user", content: judgePrompt },
    ],
    { temperature: 0.1, json: true }
  )

  const judged = parseJudgeResponse(judgeRaw)
  const eva = scoreEvaRun(goalCompleted, judged.scores_breakdown)

  return {
    eva_id: scenario.eva_id,
    domain: scenario.domain,
    domain_label: scenario.domain_label,
    scenario_name: scenario.scenario_name,
    goal_completed: goalCompleted,
    total_turns: totalTurns,
    overall_score: judged.overall_score,
    eva_a: eva.eva_a,
    eva_x: eva.eva_x,
    eva_a_pass: eva.eva_a_pass,
    eva_x_pass: eva.eva_x_pass,
    composite_pass: eva.composite_pass,
    scores_breakdown: judged.scores_breakdown,
    failure_points: judged.failure_points,
    recommendations: judged.recommendations,
    transcript,
  }
}

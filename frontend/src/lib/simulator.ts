import {
  buildCallerSystemPrompt,
  callOpenAI,
  formatTranscriptForJudge,
  JUDGE_SYSTEM_PROMPT,
  MAX_TURNS,
  parseJudgeResponse,
} from "./judge"
import type { Scenario, SimulationResult, TranscriptTurn } from "./types"

export async function runSimulation(
  apiKey: string,
  agentPrompt: string,
  scenario: Scenario
): Promise<SimulationResult> {
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
      temperature: 0.7,
    })

    transcript.push({ turn, role: "agent", content: agentText })
    agentMessages.push({ role: "assistant", content: agentText })
    callerMessages.push({ role: "user", content: agentText })

    const callerText = await callOpenAI(apiKey, callerMessages, {
      temperature: 0.8,
    })

    transcript.push({ turn, role: "caller", content: callerText })
    callerMessages.push({ role: "assistant", content: callerText })
    agentMessages.push({ role: "user", content: callerText })

    if (callerText.includes("[GOAL_ACHIEVED]")) {
      goalCompleted = true
      break
    }
    if (callerText.includes("[HANGUP]")) {
      goalCompleted = false
      break
    }
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

  return {
    run_id: 1000 + Math.floor(Math.random() * 9000),
    transcript,
    total_turns: totalTurns,
    goal_completed: goalCompleted,
    overall_score: judged.overall_score,
    scores_breakdown: judged.scores_breakdown,
    failure_points: judged.failure_points,
    recommendations: judged.recommendations,
  }
}

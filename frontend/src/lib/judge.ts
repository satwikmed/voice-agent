import type { FailurePoint, ScoresBreakdown, TranscriptTurn } from "./types"

export const OPENAI_MODEL = "gpt-4o-mini"
export const MAX_TURNS = 10

export const DIMENSION_WEIGHTS: ScoresBreakdown = {
  response_relevance: 0.2,
  objection_handling: 0.2,
  conversation_flow: 0.2,
  empathy: 0.15,
  goal_completion: 0.25,
}

export const JUDGE_SYSTEM_PROMPT = `You are a STRICT, CALIBRATED scoring judge for voice-agent conversations.

You will receive:
1. A scenario description that defines the caller's goal and personality.
2. A full conversation transcript (list of turns with role and content).

Score the AGENT's performance on each dimension below using an integer 0–100.

### Dimensions
- **response_relevance** (0-100): Did the agent's responses directly address the caller's questions and needs? Reference specific turns where the agent was on-topic or off-topic.
- **objection_handling** (0-100): How well did the agent handle pushback, complaints, or difficult questions? Cite turns where objections arose and how the agent responded.
- **conversation_flow** (0-100): Was the conversation natural and well-paced? Were there awkward pauses, repetitions, or non-sequiturs? Reference turns.
- **empathy** (0-100): Did the agent acknowledge the caller's emotions, frustrations, or concerns? Cite specific empathetic (or un-empathetic) moments by turn number.
- **goal_completion** (0-100): To what extent was the caller's stated goal achieved? 100 = fully achieved, 0 = not at all. Reference the turns that contributed to or blocked goal completion.

### Rules
- Every score MUST be justified by referencing specific turn numbers. No vibes-based scoring.
- Provide 2–4 actionable recommendations for the agent.
- Identify failure points: turns where the agent made a clear mistake.

### Output format — STRICT JSON, nothing else
Return ONLY a JSON object (no markdown fences, no commentary) with this exact schema:

{
  "response_relevance": <int 0-100>,
  "objection_handling": <int 0-100>,
  "conversation_flow": <int 0-100>,
  "empathy": <int 0-100>,
  "goal_completion": <int 0-100>,
  "overall_score": <float 0-100>,
  "failure_points": [{"turn": <int>, "reason": "<string>"}],
  "recommendations": ["<string>", ...]
}

overall_score is a weighted average:
  response_relevance × 0.20
  objection_handling × 0.20
  conversation_flow  × 0.20
  empathy            × 0.15
  goal_completion    × 0.25
`

export function buildCallerSystemPrompt(personaPrompt: string): string {
  return (
    `${personaPrompt}\n\n` +
    `--- OUTPUT RULES ---\n` +
    `You are roleplaying as a caller in a phone conversation. Respond naturally in character.\n` +
    `When you decide to hang up the phone (for any reason — frustration, rudeness, or any of your hang-up triggers), output exactly '[HANGUP]' on its own line at the END of your message.\n` +
    `When your goal has been fully achieved and you are satisfied, output exactly '[GOAL_ACHIEVED]' on its own line at the END of your message.\n` +
    `Do NOT output both tokens in the same message. Do NOT output either token unless the condition truly applies.\n` +
    `--- END OUTPUT RULES ---`
  )
}

export function computeOverallScore(scores: Partial<ScoresBreakdown>): number {
  const overall =
    (scores.response_relevance || 0) * DIMENSION_WEIGHTS.response_relevance +
    (scores.objection_handling || 0) * DIMENSION_WEIGHTS.objection_handling +
    (scores.conversation_flow || 0) * DIMENSION_WEIGHTS.conversation_flow +
    (scores.empathy || 0) * DIMENSION_WEIGHTS.empathy +
    (scores.goal_completion || 0) * DIMENSION_WEIGHTS.goal_completion

  return Math.round(overall * 100) / 100
}

export function formatTranscriptForJudge(
  scenarioDescription: string,
  transcript: TranscriptTurn[]
): string {
  const body = transcript
    .map(
      (entry) =>
        `[Turn ${entry.turn}] ${entry.role.toUpperCase()}: ${entry.content}`
    )
    .join("\n")

  return `## Scenario Description\n${scenarioDescription}\n\n## Conversation Transcript\n${body}`
}

export interface ParsedJudgeResult {
  scores_breakdown: ScoresBreakdown
  overall_score: number
  failure_points: FailurePoint[]
  recommendations: string[]
}

export function parseJudgeResponse(raw: string): ParsedJudgeResult {
  const parsed = JSON.parse(raw)
  const scores_breakdown: ScoresBreakdown = {
    response_relevance: parsed.response_relevance || 0,
    objection_handling: parsed.objection_handling || 0,
    conversation_flow: parsed.conversation_flow || 0,
    empathy: parsed.empathy || 0,
    goal_completion: parsed.goal_completion || 0,
  }

  return {
    scores_breakdown,
    overall_score: computeOverallScore(scores_breakdown),
    failure_points: parsed.failure_points || [],
    recommendations: parsed.recommendations || [],
  }
}

export async function callOpenAI(
  apiKey: string,
  messages: Array<{ role: string; content: string }>,
  options?: { temperature?: number; json?: boolean }
): Promise<string> {
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: OPENAI_MODEL,
      messages,
      temperature: options?.temperature ?? 0.7,
      ...(options?.json ? { response_format: { type: "json_object" } } : {}),
    }),
  })

  if (!response.ok) {
    const err = await response.text()
    throw new Error(`OpenAI call failed: ${err}`)
  }

  const data = await response.json()
  return data.choices[0]?.message?.content || ""
}

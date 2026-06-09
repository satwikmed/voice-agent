import { NextResponse } from "next/server"
import scenariosData from "@/data/scenarios.json"

const MAX_TURNS = 10
const OPENAI_MODEL = "gpt-4o-mini"

const JUDGE_SYSTEM_PROMPT = `You are a STRICT, CALIBRATED scoring judge for voice-agent conversations.

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

export async function POST(request: Request) {
  try {
    const { agent_prompt, scenario_id } = await request.json()
    const apiKey = process.env.OPENAI_API_KEY || ""

    if (!apiKey) {
      return NextResponse.json(
        { detail: "OPENAI_API_KEY environment variable is not configured on the Vercel deployment." },
        { status: 400 }
      )
    }

    const scenario = (scenariosData as any[]).find((s) => s.id === scenario_id)
    if (!scenario) {
      return NextResponse.json({ detail: "Scenario not found" }, { status: 404 })
    }

    const callerSystemPrompt = `${scenario.persona_prompt}\n\n` +
      `--- OUTPUT RULES ---\n` +
      `You are roleplaying as a caller in a phone conversation. Respond naturally in character.\n` +
      `When you decide to hang up the phone (for any reason — frustration, rudeness, or any of your hang-up triggers), output exactly '[HANGUP]' on its own line at the END of your message.\n` +
      `When your goal has been fully achieved and you are satisfied, output exactly '[GOAL_ACHIEVED]' on its own line at the END of your message.\n` +
      `Do NOT output both tokens in the same message. Do NOT output either token unless the condition truly applies.\n` +
      `--- END OUTPUT RULES ---`

    const agentMessages: Array<{ role: string; content: string }> = [
      { role: "system", content: agent_prompt }
    ]
    const callerMessages: Array<{ role: string; content: string }> = [
      { role: "system", content: callerSystemPrompt }
    ]

    const transcript: Array<{ turn: number; role: "agent" | "caller"; content: string }> = []
    let goalCompleted = false
    let totalTurns = 0

    // Conversation loop
    for (let turn = 1; turn <= MAX_TURNS; turn++) {
      totalTurns = turn
      
      // --- Agent turn ---
      const agentRes = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: OPENAI_MODEL,
          messages: agentMessages,
          temperature: 0.7
        })
      })

      if (!agentRes.ok) {
        const err = await agentRes.text()
        throw new Error(`OpenAI agent call failed: ${err}`)
      }

      const agentData = await agentRes.json()
      const agentText = agentData.choices[0]?.message?.content || ""
      
      transcript.push({ turn, role: "agent", content: agentText })
      agentMessages.push({ role: "assistant", content: agentText })
      callerMessages.push({ role: "user", content: agentText })

      // --- Caller turn ---
      const callerRes = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model: OPENAI_MODEL,
          messages: callerMessages,
          temperature: 0.8
        })
      })

      if (!callerRes.ok) {
        const err = await callerRes.text()
        throw new Error(`OpenAI caller call failed: ${err}`)
      }

      const callerData = await callerRes.json()
      const callerText = callerData.choices[0]?.message?.content || ""

      transcript.push({ turn, role: "caller", content: callerText })
      callerMessages.push({ role: "assistant", content: callerText })
      agentMessages.push({ role: "user", content: callerText })

      // --- Check termination ---
      if (callerText.includes("[GOAL_ACHIEVED]")) {
        goalCompleted = true
        break
      }
      if (callerText.includes("[HANGUP]")) {
        goalCompleted = false
        break
      }
    }

    // --- LLM Judge Evaluation ---
    const userPrompt = `## Scenario Description\n${scenario.scenario_description}\n\n## Conversation Transcript\n` +
      transcript.map((entry) => `[Turn ${entry.turn}] ${entry.role.toUpperCase()}: ${entry.content}`).join("\n")

    const judgeRes = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: OPENAI_MODEL,
        messages: [
          { role: "system", content: JUDGE_SYSTEM_PROMPT },
          { role: "user", content: userPrompt }
        ],
        temperature: 0.1,
        response_format: { type: "json_object" }
      })
    })

    if (!judgeRes.ok) {
      const err = await judgeRes.text()
      throw new Error(`OpenAI judge call failed: ${err}`)
    }

    const judgeData = await judgeRes.json()
    const rawJudgeJson = judgeData.choices[0]?.message?.content || "{}"
    let parsedJudge = JSON.parse(rawJudgeJson)

    // Recompute overall_score to guarantee correctness
    const weights = {
      response_relevance: 0.20,
      objection_handling: 0.20,
      conversation_flow: 0.20,
      empathy: 0.15,
      goal_completion: 0.25
    }

    const overallScore = 
      (parsedJudge.response_relevance || 0) * weights.response_relevance +
      (parsedJudge.objection_handling || 0) * weights.objection_handling +
      (parsedJudge.conversation_flow || 0) * weights.conversation_flow +
      (parsedJudge.empathy || 0) * weights.empathy +
      (parsedJudge.goal_completion || 0) * weights.goal_completion

    parsedJudge.overall_score = Math.round(overallScore * 100) / 100

    const finalResult = {
      run_id: 1000 + Math.floor(Math.random() * 9000),
      transcript,
      total_turns: totalTurns,
      goal_completed: goalCompleted,
      overall_score: parsedJudge.overall_score,
      scores_breakdown: {
        response_relevance: parsedJudge.response_relevance || 0,
        objection_handling: parsedJudge.objection_handling || 0,
        conversation_flow: parsedJudge.conversation_flow || 0,
        empathy: parsedJudge.empathy || 0,
        goal_completion: parsedJudge.goal_completion || 0
      },
      failure_points: parsedJudge.failure_points || [],
      recommendations: parsedJudge.recommendations || []
    }

    return NextResponse.json(finalResult)
  } catch (error: any) {
    console.error("Simulation endpoint error:", error)
    return NextResponse.json({ detail: error.message || "An unexpected error occurred during simulation." }, { status: 500 })
  }
}

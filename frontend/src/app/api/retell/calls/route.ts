import { NextRequest, NextResponse } from "next/server"
import {
  formatTranscriptForJudge,
  JUDGE_SYSTEM_PROMPT,
  callOpenAI,
  parseJudgeResponse,
} from "@/lib/judge"
import { getRetellCall, listRetellCalls } from "@/lib/retell-client"

function getApiKey(request: NextRequest): string | null {
  return request.headers.get("x-retell-api-key")
}

export async function GET(request: NextRequest) {
  const apiKey = getApiKey(request)
  if (!apiKey) {
    return NextResponse.json(
      { detail: "Missing x-retell-api-key header." },
      { status: 401 }
    )
  }

  try {
    const calls = await listRetellCalls(apiKey, 25)
    return NextResponse.json({ calls })
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "Failed to list Retell calls."
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}

export async function POST(request: NextRequest) {
  const apiKey = getApiKey(request)
  const openAiKey = process.env.OPENAI_API_KEY || ""

  if (!apiKey) {
    return NextResponse.json(
      { detail: "Missing x-retell-api-key header." },
      { status: 401 }
    )
  }

  if (!openAiKey) {
    return NextResponse.json(
      { detail: "OPENAI_API_KEY is not configured on this deployment." },
      { status: 400 }
    )
  }

  try {
    const { call_id } = await request.json()
    if (!call_id) {
      return NextResponse.json({ detail: "call_id is required." }, { status: 400 })
    }

    const call = await getRetellCall(apiKey, call_id)
    if (!call.transcript?.length) {
      return NextResponse.json(
        { detail: "Call has no structured transcript to evaluate." },
        { status: 422 }
      )
    }

    const judgePrompt = formatTranscriptForJudge(
      `Production Retell call ${call.call_id}${call.agent_name ? ` (${call.agent_name})` : ""}. Evaluate the deployed agent's performance on this real call transcript.`,
      call.transcript
    )

    const judgeRaw = await callOpenAI(
      openAiKey,
      [
        { role: "system", content: JUDGE_SYSTEM_PROMPT },
        { role: "user", content: judgePrompt },
      ],
      { temperature: 0.1, json: true }
    )

    const judged = parseJudgeResponse(judgeRaw)

    return NextResponse.json({
      call,
      evaluation: judged,
    })
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "Failed to evaluate Retell call."
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}

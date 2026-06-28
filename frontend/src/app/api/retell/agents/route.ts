import { NextRequest, NextResponse } from "next/server"
import {
  getRetellAgentPrompt,
  listRetellAgents,
} from "@/lib/retell-client"

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
    const agents = await listRetellAgents(apiKey)
    return NextResponse.json({ agents })
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "Failed to list Retell agents."
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}

export async function POST(request: NextRequest) {
  const apiKey = getApiKey(request)
  if (!apiKey) {
    return NextResponse.json(
      { detail: "Missing x-retell-api-key header." },
      { status: 401 }
    )
  }

  try {
    const { agent_id } = await request.json()
    if (!agent_id) {
      return NextResponse.json({ detail: "agent_id is required." }, { status: 400 })
    }

    const imported = await getRetellAgentPrompt(apiKey, agent_id)
    return NextResponse.json(imported)
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "Failed to import Retell agent."
    return NextResponse.json({ detail: message }, { status: 502 })
  }
}

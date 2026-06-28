import type { RetellAgentSummary, TranscriptTurn } from "./types"

const RETELL_BASE = "https://api.retellai.com"

function retellHeaders(apiKey: string): HeadersInit {
  return {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  }
}

export async function listRetellAgents(apiKey: string): Promise<RetellAgentSummary[]> {
  const response = await fetch(`${RETELL_BASE}/list-agents?limit=100`, {
    headers: retellHeaders(apiKey),
  })

  if (!response.ok) {
    const err = await response.text()
    throw new Error(`Retell list-agents failed (${response.status}): ${err}`)
  }

  const agents = await response.json()
  return (agents as Array<Record<string, unknown>>).map((agent) => ({
    agent_id: String(agent.agent_id),
    agent_name: String(agent.agent_name || "Unnamed agent"),
    version: typeof agent.version === "number" ? agent.version : undefined,
    response_engine_type:
      typeof agent.response_engine === "object" &&
      agent.response_engine &&
      "type" in agent.response_engine
        ? String((agent.response_engine as { type?: string }).type)
        : undefined,
  }))
}

export async function getRetellAgentPrompt(
  apiKey: string,
  agentId: string
): Promise<{ agent_name: string; prompt: string; begin_message?: string }> {
  const agentRes = await fetch(`${RETELL_BASE}/get-agent/${agentId}`, {
    headers: retellHeaders(apiKey),
  })

  if (!agentRes.ok) {
    const err = await agentRes.text()
    throw new Error(`Retell get-agent failed (${agentRes.status}): ${err}`)
  }

  const agent = await agentRes.json()
  const engine = agent.response_engine as { type?: string; llm_id?: string }

  if (engine?.type !== "retell-llm" || !engine.llm_id) {
    throw new Error(
      "Agent uses a conversation-flow engine. VoiceIQ currently imports retell-llm general prompts only."
    )
  }

  const llmRes = await fetch(`${RETELL_BASE}/get-retell-llm/${engine.llm_id}`, {
    headers: retellHeaders(apiKey),
  })

  if (!llmRes.ok) {
    const err = await llmRes.text()
    throw new Error(`Retell get-retell-llm failed (${llmRes.status}): ${err}`)
  }

  const llm = await llmRes.json()

  return {
    agent_name: String(agent.agent_name || agentId),
    prompt: String(llm.general_prompt || ""),
    begin_message: llm.begin_message ? String(llm.begin_message) : undefined,
  }
}

export interface RetellCallRecord {
  call_id: string
  agent_id?: string
  agent_name?: string
  start_timestamp?: number
  duration_ms?: number
  call_status?: string
  transcript?: TranscriptTurn[]
  raw_transcript?: string
}

function mapRetellTranscript(
  transcriptObject: Array<{ role?: string; content?: string; words?: string }>
): TranscriptTurn[] {
  return transcriptObject.map((entry, index) => ({
    turn: Math.ceil((index + 1) / 2) || 1,
    role: entry.role === "agent" ? "agent" : "caller",
    content: entry.content || entry.words || "",
  }))
}

export async function listRetellCalls(
  apiKey: string,
  limit = 20
): Promise<RetellCallRecord[]> {
  const response = await fetch(`${RETELL_BASE}/v2/list-calls`, {
    method: "POST",
    headers: retellHeaders(apiKey),
    body: JSON.stringify({ limit }),
  })

  if (!response.ok) {
    const err = await response.text()
    throw new Error(`Retell list-calls failed (${response.status}): ${err}`)
  }

  const payload = await response.json()
  const calls = Array.isArray(payload) ? payload : payload.calls || []

  return calls.slice(0, limit).map((call: Record<string, unknown>) => ({
    call_id: String(call.call_id),
    agent_id: call.agent_id ? String(call.agent_id) : undefined,
    agent_name: call.agent_name ? String(call.agent_name) : undefined,
    start_timestamp:
      typeof call.start_timestamp === "number"
        ? call.start_timestamp
        : undefined,
    duration_ms:
      typeof call.duration_ms === "number" ? call.duration_ms : undefined,
    call_status: call.call_status ? String(call.call_status) : undefined,
  }))
}

export async function getRetellCall(
  apiKey: string,
  callId: string
): Promise<RetellCallRecord> {
  const response = await fetch(`${RETELL_BASE}/v2/get-call/${callId}`, {
    headers: retellHeaders(apiKey),
  })

  if (!response.ok) {
    const err = await response.text()
    throw new Error(`Retell get-call failed (${response.status}): ${err}`)
  }

  const call = await response.json()
  const transcriptObject = call.transcript_object as
    | Array<{ role?: string; content?: string; words?: string }>
    | undefined

  const transcript = transcriptObject?.length
    ? mapRetellTranscript(transcriptObject)
    : undefined

  return {
    call_id: String(call.call_id),
    agent_id: call.agent_id ? String(call.agent_id) : undefined,
    agent_name: call.agent_name ? String(call.agent_name) : undefined,
    start_timestamp:
      typeof call.start_timestamp === "number"
        ? call.start_timestamp
        : undefined,
    duration_ms:
      typeof call.duration_ms === "number" ? call.duration_ms : undefined,
    call_status: call.call_status ? String(call.call_status) : undefined,
    transcript,
    raw_transcript: call.transcript ? String(call.transcript) : undefined,
  }
}

import { NextResponse } from "next/server"
import scenariosData from "@/data/scenarios.json"
import { runSimulation } from "@/lib/simulator"
import type { Scenario } from "@/lib/types"

export async function POST(request: Request) {
  try {
    const { agent_prompt, scenario_id } = await request.json()
    const apiKey = process.env.OPENAI_API_KEY || ""

    if (!apiKey) {
      return NextResponse.json(
        {
          detail:
            "OPENAI_API_KEY is not configured on this deployment. Add it in Vercel environment variables.",
        },
        { status: 400 }
      )
    }

    const scenario = (scenariosData as Scenario[]).find(
      (s) => s.id === scenario_id
    )
    if (!scenario) {
      return NextResponse.json({ detail: "Scenario not found" }, { status: 404 })
    }

    const result = await runSimulation(apiKey, agent_prompt, scenario)
    return NextResponse.json(result)
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "Simulation failed unexpectedly."
    console.error("Simulation endpoint error:", error)
    return NextResponse.json({ detail: message }, { status: 500 })
  }
}

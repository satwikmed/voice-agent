import { NextResponse } from "next/server"
import scenariosData from "@/data/scenarios.json"
import { runSimulation } from "@/lib/simulator"
import type { Scenario } from "@/lib/types"

export async function POST(request: Request) {
  try {
    const { agent_prompt, scenario_ids } = await request.json()
    const apiKey = process.env.OPENAI_API_KEY || ""

    if (!apiKey) {
      return NextResponse.json(
        { detail: "OPENAI_API_KEY is not configured on this deployment." },
        { status: 400 }
      )
    }

    const ids: number[] = Array.isArray(scenario_ids)
      ? scenario_ids
      : (scenariosData as Scenario[]).map((s) => s.id)

    const scenarios = (scenariosData as Scenario[]).filter((s) =>
      ids.includes(s.id)
    )

    const results = []
    for (const scenario of scenarios) {
      const result = await runSimulation(apiKey, agent_prompt, scenario)
      results.push({
        scenario_id: scenario.id,
        scenario_name: scenario.scenario_name,
        difficulty_level: scenario.difficulty_level,
        ...result,
      })
    }

    const passed = results.filter((r) => r.overall_score >= 70).length
    const passRate = results.length === 0 ? 0 : passed / results.length

    return NextResponse.json({
      results,
      summary: {
        total: results.length,
        passed,
        pass_rate: Math.round(passRate * 100) / 100,
        average_score:
          results.length === 0
            ? 0
            : Math.round(
                (results.reduce((acc, r) => acc + r.overall_score, 0) /
                  results.length) *
                  10
              ) / 10,
      },
    })
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "Batch simulation failed."
    console.error("Batch endpoint error:", error)
    return NextResponse.json({ detail: message }, { status: 500 })
  }
}

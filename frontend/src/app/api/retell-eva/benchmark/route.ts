import { NextResponse } from "next/server"
import evaData from "@/data/eva-scenarios.json"
import seedResults from "@/data/eva-benchmark-results.json"
import { runEvaSimulation } from "@/lib/eva-simulator"
import { aggregateEvaBenchmark, type EvaScenario } from "@/lib/retell-eva"

export async function GET() {
  return NextResponse.json(seedResults)
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const apiKey = process.env.OPENAI_API_KEY || ""
    const {
      eva_id,
      domain,
      limit = 3,
      agent_prompt,
      mode = "single",
    } = body as {
      eva_id?: string
      domain?: string
      limit?: number
      agent_prompt?: string
      mode?: "single" | "suite"
    }

    if (!apiKey) {
      return NextResponse.json(
        {
          detail:
            "OPENAI_API_KEY not configured. Showing seeded benchmark results — add API key for live runs.",
          seeded: true,
          ...seedResults,
        },
        { status: 200 }
      )
    }

    const scenarios = (evaData as { scenarios: EvaScenario[] }).scenarios
    let selected = scenarios

    if (eva_id) {
      selected = scenarios.filter((s) => s.eva_id === eva_id)
    } else if (domain) {
      selected = scenarios.filter((s) => s.domain === domain)
    }

    if (mode === "suite") {
      selected = selected.slice(0, Math.min(limit, selected.length))
    } else {
      selected = selected.slice(0, 1)
    }

    if (selected.length === 0) {
      return NextResponse.json({ detail: "No matching EVA scenarios" }, { status: 404 })
    }

    const runs = []
    for (const scenario of selected) {
      const result = await runEvaSimulation(apiKey, scenario, agent_prompt)
      runs.push(result)
    }

    const summary = aggregateEvaBenchmark(runs)

    return NextResponse.json({
      seeded: false,
      summary,
      runs,
      key_findings: generateFindings(summary),
    })
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "EVA benchmark failed unexpectedly."
    console.error("RetellEVA benchmark error:", error)
    return NextResponse.json({ detail: message }, { status: 500 })
  }
}

function generateFindings(summary: ReturnType<typeof aggregateEvaBenchmark>): string[] {
  const findings: string[] = []
  findings.push(
    `Composite pass@1: ${Math.round(summary.composite_pass_at_1 * 100)}% across ${summary.scenario_count} EVA-Bench scenarios.`
  )
  for (const [domain, stats] of Object.entries(summary.by_domain)) {
    findings.push(
      `${domain}: EVA-A ${stats.avg_eva_a.toFixed(2)} / EVA-X ${stats.avg_eva_x.toFixed(2)} (pass ${Math.round(stats.composite_pass_at_1 * 100)}%).`
    )
  }
  if (summary.avg_eva_x > summary.avg_eva_a) {
    findings.push(
      "EVA-X exceeds EVA-A — agents sound acceptable but fail task completion (matches EVA paper pattern)."
    )
  }
  return findings
}

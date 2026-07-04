import { NextResponse } from "next/server"
import evaData from "@/data/eva-scenarios.json"
import type { EvaScenario } from "@/lib/voiceiq-eva"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const domain = searchParams.get("domain")

  let scenarios = (evaData as { scenarios: EvaScenario[] }).scenarios
  if (domain) {
    scenarios = scenarios.filter((s) => s.domain === domain)
  }

  return NextResponse.json({
    source: (evaData as { source: string }).source,
    license: (evaData as { license: string }).license,
    scenario_count: scenarios.length,
    scenarios,
  })
}

import { NextResponse } from "next/server"
import scenarios from "@/data/scenarios.json"

export async function GET() {
  return NextResponse.json(scenarios)
}

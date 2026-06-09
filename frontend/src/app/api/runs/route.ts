import { NextResponse } from "next/server"
import runs from "@/data/runs.json"

export async function GET() {
  return NextResponse.json(runs)
}

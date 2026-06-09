import { NextResponse } from "next/server"
import runDetails from "@/data/run_details.json"

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const details = (runDetails as Record<string, any>)[id]
  
  if (!details) {
    return NextResponse.json({ detail: "Run not found" }, { status: 404 })
  }
  
  return NextResponse.json(details)
}

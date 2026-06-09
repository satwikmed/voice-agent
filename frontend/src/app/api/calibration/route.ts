import { NextResponse } from "next/server"
import calibration from "@/data/calibration.json"

export async function GET() {
  return NextResponse.json(calibration)
}

import type { EvaDomain } from "./voiceiq-eva"

/** Retell-compatible LLM config snippet for dashboard import / copy-paste. */
export function buildRetellLlmExport(
  generalPrompt: string,
  domain: EvaDomain
): Record<string, unknown> {
  return {
    _voiceiq_eva_meta: {
      exported_at: new Date().toISOString(),
      eva_domain: domain,
      certification: "VoiceIQ EVA scenario-grounded prompt",
      disclaimer:
        "Independent export — not affiliated with Retell AI, Inc.",
    },
    general_prompt: generalPrompt.trim(),
    model: "gpt-4o-mini",
    model_temperature: 0.3,
    begin_message: null,
    general_tools: [],
  }
}

export function downloadRetellExport(
  generalPrompt: string,
  domain: EvaDomain,
  filename = "voiceiq-eva-retell-llm.json"
): void {
  const payload = buildRetellLlmExport(generalPrompt, domain)
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

# RetellEVA

**Pre-launch QA for Retell AI voice agents, benchmarked on [EVA-Bench](https://huggingface.co/datasets/ServiceNow-AI/eva-bench) (Hugging Face).**

Retell Assure covers post-launch QA. RetellEVA covers pre-launch — before a single production call.

## What it does

| Layer | Description |
|---|---|
| **HF benchmark** | 15 curated scenarios from ServiceNow EVA-Bench (airline, healthcare HR, ITSM) |
| **Retell integration** | Domain-specific agent prompts + Retell API import (existing VoiceIQ portal) |
| **Scoring** | EVA-A (accuracy) + EVA-X (experience), aligned with EVA-Bench composite metrics |
| **Deploy gate** | Block launch below 60% composite pass@1 across domains |
| **Publish** | HF Space demo + seeded results for portfolio without API keys |

## Hugging Face task mapping

| HF Task | Role in RetellEVA |
|---|---|
| [audio-text-to-text](https://huggingface.co/tasks/audio-text-to-text) | Voice agent evaluation (primary) |
| [automatic-speech-recognition](https://huggingface.co/tasks/automatic-speech-recognition) | Cascade layer (Retell STT) |
| [text-to-speech](https://huggingface.co/tasks/text-to-speech) | Cascade layer (Retell TTS) |

Benchmark dataset: [ServiceNow-AI/eva-bench](https://huggingface.co/datasets/ServiceNow-AI/eva-bench)

## Quick start

```bash
# Sync latest EVA scenarios from Hugging Face (optional — 15 bundled by default)
python scripts/sync_eva_scenarios.py

# Run benchmark (requires OPENAI_API_KEY in .env)
python scripts/run_retell_eva.py --domain airline_csm --limit 3 -v

# Frontend portal (RetellEVA tab)
cd frontend && npm run dev
# → http://localhost:3000/portal

# Hugging Face Space demo
streamlit run huggingface-space/app.py
```

## Key findings (seeded demo run)

| Domain | EVA-A avg | EVA-X avg | Composite pass@1 |
|---|---|---|---|
| Airline CSM | 74.8% | 78.2% | **80%** |
| Healthcare HR | 51.2% | 69.8% | **40%** |
| Enterprise ITSM | 57.6% | 69.2% | **20%** |

**Insight:** Default Retell-style prompts pass airline rebooking but fail healthcare credentialing and ITSM incident workflows — exactly the enterprise verticals Retell sells into.

## Architecture

```
EVA-Bench (HF) → retell_eva/loader → VoiceIQ simulator → LLM judge → EVA-A/EVA-X scores
                                              ↑
                                    Retell agent prompt (domain-specific)
```

## Live demo

- **Portal:** https://voice-agent-amber-nine.vercel.app/portal → RetellEVA tab
- **GitHub:** https://github.com/satwikmed/voice-agent
- **HF Space:** https://huggingface.co/spaces/satwikmed/retell-eva (deploy with `HF_TOKEN=... python scripts/deploy_hf_space.py`)

## Outreach to Retell AI

**Subject:** Open-source EVA-Bench adapter for Retell — pre-launch QA results

> Hi [name],
>
> I built RetellEVA — an open-source adapter that runs Retell-style agent prompts against ServiceNow's EVA-Bench (213 enterprise scenarios on Hugging Face).
>
> Key finding on default prompts: 80% composite pass on airline, 40% on healthcare HR, 20% on ITSM — EVA-X exceeds EVA-A on every domain (agents sound fine but fail task completion).
>
> Live demo: [your HF Space or Vercel URL]
> Repo: [GitHub URL]
>
> This fills the pre-launch gap alongside Retell Assure. Happy to contribute to your ecosystem or walk through findings.

**Where to send:** support@retellai.com, LinkedIn DM to Retell eng/founders, apply at [retellai.com/careers](https://www.retellai.com/careers) with this as lead project.

## License

MIT (EVA-Bench data: MIT per ServiceNow)

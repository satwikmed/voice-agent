# 🎙️ VoiceIQ

*A calibrated testing harness for AI voice agents — score, find failures, and prove your judge is trustworthy before you ship.*

## What This Is

VoiceIQ simulates realistic caller-agent conversations using two LLMs (one plays the caller, one plays the agent), then evaluates every conversation with a calibrated LLM judge that produces per-dimension scores with turn-level evidence. It includes a human calibration framework that statistically validates how much you should trust the judge — so you're not shipping on vibes.

## Key Features

- **6 realistic test scenarios** spanning easy (friendly inquiry) to hard (hostile caller with hang-up trigger)
- **Two-LLM conversation simulator** — caller and agent personas driven by Ollama, producing natural multi-turn transcripts
- **Calibrated LLM judge** with structured scoring, failure point identification, and self-consistency checking (3x eval per transcript)
- **Human calibration harness** — compute MAE, Pearson r, Spearman ρ, Bland-Altman bias, failure point precision/recall/Jaccard
- **Streamlit dashboard** with pre-loaded demo data — deploy publicly without Ollama

## Architecture

```
voice/
├── database/          # SQLite init & seed scripts
│   ├── init_db.py
│   └── seed_data.py
├── simulator/         # Conversation engine & judge
│   ├── scenarios.py
│   ├── agent_simulator.py
│   └── judge.py
├── calibration/       # Human calibration tools
│   ├── harness.py
│   └── report.py
├── dashboard/         # Streamlit app
│   └── app.py
├── tests/             # pytest suite
├── FINDINGS.md        # Methodology & results
└── README.md
```

**`database/`** — Initializes the SQLite database and seeds it with pre-generated transcripts, judge scores, and calibration data. The seed data powers the public demo.

**`simulator/`** — Defines the 6 test scenarios, runs two-LLM conversations, and evaluates transcripts with the judge. Requires a local Ollama instance.

**`calibration/`** — Interactive harness for human grading and statistical agreement reporting between human and judge scores.

**`dashboard/`** — Streamlit app for exploring results, comparing scenarios, and viewing calibration metrics.

## Quick Start

```bash
# 1. Install Ollama and pull the model
ollama pull llama3:8b

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Initialize and seed the database
python database/init_db.py
python database/seed_data.py

# 4. Launch the dashboard
streamlit run dashboard/app.py
```

## Streamlit Cloud Deployment

The seeded database contains pre-generated transcripts and judge scores — the public demo runs entirely from this data. No Ollama required.

The **Run a Test** tab (live conversation generation) only works locally with Ollama installed.

To deploy:

1. Fork this repo
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud)
3. No secrets or environment variables needed
4. Deploy

Create `.streamlit/config.toml` for consistent theming:

```toml
[theme]
base = "dark"
primaryColor = "#FF6B6B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
```

## Running Tests

```bash
pytest tests/ -v
```

## Calibration Workflow

```bash
# Grade transcripts manually (interactive CLI)
python calibration/harness.py -n 10

# Generate calibration report (MAE, Pearson r, Bland-Altman, etc.)
python calibration/report.py
```

See [FINDINGS.md](FINDINGS.md) for methodology details and metric definitions.

## Tech Stack

| Component | Technology |
|---|---|
| LLM Runtime | Ollama (llama3:8b) |
| Database | SQLite |
| Dashboard | Streamlit + Plotly |
| Language | Python 3.10+ |
| Testing | pytest |

## License

MIT

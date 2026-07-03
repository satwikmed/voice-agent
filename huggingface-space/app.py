"""
RetellEVA — Hugging Face Space entry point.

Minimal Streamlit demo for EVA-Bench pre-launch QA. Full UI lives in the
Next.js portal (/portal → RetellEVA tab) or dashboard/app.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from retell_eva.loader import load_eva_scenarios  # noqa: E402
from retell_eva.scorer import aggregate_benchmark  # noqa: E402

SEED_PATH = PROJECT_ROOT / "frontend" / "src" / "data" / "eva-benchmark-results.json"

st.set_page_config(page_title="RetellEVA", page_icon="🎙️", layout="wide")

st.title("RetellEVA")
st.caption(
    "Pre-launch QA for Retell AI voice agents · "
    "[EVA-Bench on Hugging Face](https://huggingface.co/datasets/ServiceNow-AI/eva-bench)"
)

col1, col2, col3 = st.columns(3)

seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
summary = seed["summary"]

col1.metric("EVA-A pass@1", f"{summary['eva_a_pass_at_1']:.0%}")
col2.metric("EVA-X pass@1", f"{summary['eva_x_pass_at_1']:.0%}")
col3.metric("Composite pass@1", f"{summary['composite_pass_at_1']:.0%}")

st.subheader("Domain breakdown")
for domain, stats in summary["by_domain"].items():
    st.progress(stats["composite_pass_at_1"], text=f"{domain}: {stats['composite_pass_at_1']:.0%} pass")

st.subheader("Key findings")
for finding in seed.get("key_findings", []):
    st.markdown(f"- {finding}")

st.subheader("EVA-Bench scenarios (bundled subset)")
scenarios = load_eva_scenarios()
domain_filter = st.selectbox(
    "Domain",
    ["all", "airline_csm", "healthcare_hrsd", "enterprise_itsm"],
)
filtered = scenarios if domain_filter == "all" else [s for s in scenarios if s.domain == domain_filter]

for scenario in filtered[:5]:
    with st.expander(f"{scenario.eva_id} — {scenario.domain_label}"):
        st.write(scenario.caller_goal)
        st.code(scenario.starting_utterance)

st.info(
    "Complements Retell Assure (post-launch). "
    "Full benchmark runner: `python scripts/run_retell_eva.py`"
)

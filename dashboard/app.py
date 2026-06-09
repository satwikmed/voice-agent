"""
VoiceIQ Dashboard
=================

A Streamlit-based dashboard for VoiceIQ — the calibrated testing harness
for AI voice agents. Dark-themed, Plotly-powered, production-quality.

Tabs:
1. Judge Calibration — credibility-first: human-vs-judge agreement metrics
2. Run a Test — simulate conversations and see evaluation results
3. Test History — browse and analyze past runs
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "voiceiq.db"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Brand colours ─────────────────────────────────────────────────────────────
BRAND = {
    "primary": "#6C63FF",
    "secondary": "#FF6584",
    "accent": "#43E97B",
    "warning": "#FFB74D",
    "danger": "#FF5252",
    "surface": "#1A1D23",
    "bg": "#0E1117",
    "text": "#FAFAFA",
    "muted": "#8B8D97",
}

DIMENSION_COLORS = {
    "response_relevance": "#6C63FF",
    "objection_handling": "#FF6584",
    "conversation_flow": "#43E97B",
    "empathy": "#FFB74D",
    "goal_completion": "#36D7B7",
}

# ── Database helpers ──────────────────────────────────────────────────────────

def get_db_connection() -> sqlite3.Connection:
    """Return a database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all_runs() -> pd.DataFrame:
    """Fetch all test runs joined with scenario info."""
    conn = get_db_connection()
    df = pd.read_sql_query(
        """
        SELECT tr.*, ts.scenario_name, ts.difficulty_level, ts.caller_personality
        FROM test_runs tr
        JOIN test_scenarios ts ON tr.scenario_id = ts.id
        ORDER BY tr.created_at DESC
        """,
        conn,
    )
    conn.close()
    return df


def fetch_run_detail(run_id: int) -> dict[str, Any] | None:
    """Fetch a single test run with full detail."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT tr.*, ts.scenario_name, ts.scenario_description,
               ts.difficulty_level, ts.caller_personality
        FROM test_runs tr
        JOIN test_scenarios ts ON tr.scenario_id = ts.id
        WHERE tr.id = ?
        """,
        (run_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def fetch_scenarios() -> list[dict[str, Any]]:
    """Fetch all test scenarios."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_scenarios ORDER BY id")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def fetch_calibration_data() -> pd.DataFrame:
    """Fetch calibration entries joined with test run scores."""
    conn = get_db_connection()
    df = pd.read_sql_query(
        """
        SELECT jc.*, tr.overall_score as run_overall_score,
               tr.scores_breakdown, tr.failure_points as run_failure_points,
               ts.scenario_name
        FROM judge_calibration jc
        JOIN test_runs tr ON jc.test_run_id = tr.id
        JOIN test_scenarios ts ON tr.scenario_id = ts.id
        WHERE jc.human_score IS NOT NULL
        ORDER BY jc.created_at
        """,
        conn,
    )
    conn.close()
    return df


# ── Plotly theme ──────────────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=BRAND["text"], family="Inter, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
)


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent dark theme to a Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)")
    return fig


# ── Score colour helper ───────────────────────────────────────────────────────

def score_color(score: float) -> str:
    """Return green/amber/red based on score threshold."""
    if score >= 80:
        return BRAND["accent"]
    elif score >= 60:
        return BRAND["warning"]
    return BRAND["danger"]


def score_badge(score: float, label: str = "") -> str:
    """Return an HTML badge for a score."""
    color = score_color(score)
    return (
        f'<div style="display:inline-block; background:{color}22; border:1px solid {color}; '
        f'border-radius:8px; padding:8px 16px; margin:4px; text-align:center;">'
        f'<div style="font-size:28px; font-weight:700; color:{color};">{score:.0f}</div>'
        f'<div style="font-size:11px; color:{BRAND["muted"]}; text-transform:uppercase; '
        f'letter-spacing:1px;">{label}</div></div>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="VoiceIQ — Voice Agent Testing Harness",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global */
        html, body, [class*="st-"] {{
            font-family: 'Inter', sans-serif;
        }}
        .stApp {{
            background: {BRAND["bg"]};
        }}

        /* Header */
        .hero {{
            background: linear-gradient(135deg, {BRAND["primary"]}15, {BRAND["secondary"]}10);
            border: 1px solid {BRAND["primary"]}30;
            border-radius: 16px;
            padding: 32px 40px;
            margin-bottom: 24px;
        }}
        .hero h1 {{
            margin: 0;
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, {BRAND["primary"]}, {BRAND["secondary"]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .hero p {{
            margin: 8px 0 0;
            color: {BRAND["muted"]};
            font-size: 15px;
        }}

        /* Metric cards */
        .metric-card {{
            background: {BRAND["surface"]};
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 20px 24px;
            text-align: center;
        }}
        .metric-card .value {{
            font-size: 36px;
            font-weight: 700;
            margin: 4px 0;
        }}
        .metric-card .label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: {BRAND["muted"]};
        }}

        /* Transcript */
        .turn-agent {{
            background: {BRAND["primary"]}15;
            border-left: 3px solid {BRAND["primary"]};
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin: 6px 0;
        }}
        .turn-caller {{
            background: {BRAND["secondary"]}12;
            border-left: 3px solid {BRAND["secondary"]};
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin: 6px 0;
        }}
        .turn-failure {{
            border: 1px solid {BRAND["danger"]}80;
            background: {BRAND["danger"]}15;
        }}
        .turn-label {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }}

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            padding: 10px 20px;
        }}

        /* Hide streamlit elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

        /* Scrollable transcript */
        .transcript-container {{
            max-height: 500px;
            overflow-y: auto;
            padding-right: 8px;
        }}

        /* Status badges */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-success {{ background: {BRAND["accent"]}22; color: {BRAND["accent"]}; border: 1px solid {BRAND["accent"]}40; }}
        .badge-warning {{ background: {BRAND["warning"]}22; color: {BRAND["warning"]}; border: 1px solid {BRAND["warning"]}40; }}
        .badge-danger {{ background: {BRAND["danger"]}22; color: {BRAND["danger"]}; border: 1px solid {BRAND["danger"]}40; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <h1>🎙️ VoiceIQ</h1>
        <p>A calibrated testing harness for AI voice agents — score, find failures,
        and prove your judge is trustworthy before you ship.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

tab_calibration, tab_run, tab_history = st.tabs([
    "🎯 Judge Calibration",
    "🚀 Run a Test",
    "📊 Test History",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: JUDGE CALIBRATION
# ══════════════════════════════════════════════════════════════════════════════

with tab_calibration:
    st.markdown("### Judge Calibration Dashboard")
    st.markdown(
        f'<p style="color:{BRAND["muted"]}; margin-top:-8px;">'
        "How trustworthy is the LLM judge? This tab compares judge scores against "
        "human ground-truth to surface systematic biases and reliability limits.</p>",
        unsafe_allow_html=True,
    )

    cal_df = fetch_calibration_data()

    if cal_df.empty:
        st.warning("No calibration data available. Run `python calibration/harness.py` to grade transcripts.")
    else:
        # ── Compute metrics ───────────────────────────────────────────────
        from scipy import stats as scipy_stats

        human_scores = cal_df["human_score"].values
        judge_scores = cal_df["judge_score"].values
        diffs = judge_scores - human_scores
        means = (judge_scores + human_scores) / 2

        mae = float(np.mean(np.abs(diffs)))
        bias = float(np.mean(diffs))
        sd = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0
        upper_loa = bias + 1.96 * sd
        lower_loa = bias - 1.96 * sd

        pearson_r, pearson_p = scipy_stats.pearsonr(human_scores, judge_scores) if len(human_scores) >= 3 else (None, None)
        spearman_rho, spearman_p = scipy_stats.spearmanr(human_scores, judge_scores) if len(human_scores) >= 3 else (None, None)

        # ── Failure point overlap ─────────────────────────────────────────
        precision_vals, recall_vals, jaccard_vals = [], [], []
        for _, row in cal_df.iterrows():
            try:
                human_fp = set(json.loads(row["human_failure_points"])) if row["human_failure_points"] else set()
                run_fp_raw = json.loads(row["run_failure_points"]) if row["run_failure_points"] else []
                judge_fp = set()
                for fp in run_fp_raw:
                    if isinstance(fp, dict) and "turn" in fp:
                        judge_fp.add(fp["turn"])
                    elif isinstance(fp, int):
                        judge_fp.add(fp)

                if human_fp or judge_fp:
                    intersection = human_fp & judge_fp
                    union = human_fp | judge_fp
                    precision_vals.append(len(intersection) / len(judge_fp) if judge_fp else 1.0)
                    recall_vals.append(len(intersection) / len(human_fp) if human_fp else 1.0)
                    jaccard_vals.append(len(intersection) / len(union) if union else 1.0)
            except (json.JSONDecodeError, TypeError):
                continue

        fp_precision = float(np.mean(precision_vals)) if precision_vals else None
        fp_recall = float(np.mean(recall_vals)) if recall_vals else None
        fp_jaccard = float(np.mean(jaccard_vals)) if jaccard_vals else None

        # ── Summary metrics row ───────────────────────────────────────────
        cols = st.columns(5)
        metrics = [
            ("MAE", f"{mae:.1f}", "Mean Absolute Error", BRAND["primary"]),
            ("Pearson r", f"{pearson_r:.3f}" if pearson_r else "N/A", "Linear Correlation", BRAND["accent"]),
            ("Spearman ρ", f"{spearman_rho:.3f}" if spearman_rho else "N/A", "Rank Correlation", BRAND["secondary"]),
            ("Bias", f"{bias:+.1f}", "Judge − Human Mean", BRAND["warning"]),
            ("N", f"{len(cal_df)}", "Calibration Pairs", BRAND["muted"]),
        ]
        for col, (label, value, desc, color) in zip(cols, metrics):
            col.markdown(
                f"""<div class="metric-card">
                    <div class="label">{desc}</div>
                    <div class="value" style="color:{color};">{value}</div>
                    <div class="label">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Charts row ────────────────────────────────────────────────────
        col_scatter, col_bland = st.columns(2)

        with col_scatter:
            st.markdown("#### Human vs Judge Score Correlation")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=human_scores,
                y=judge_scores,
                mode="markers",
                marker=dict(
                    size=10,
                    color=BRAND["primary"],
                    line=dict(width=1, color=BRAND["text"]),
                    opacity=0.8,
                ),
                text=cal_df["scenario_name"],
                hovertemplate="<b>%{text}</b><br>Human: %{x:.0f}<br>Judge: %{y:.0f}<extra></extra>",
            ))
            # Perfect agreement line
            min_val = min(min(human_scores), min(judge_scores)) - 5
            max_val = max(max(human_scores), max(judge_scores)) + 5
            fig.add_trace(go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode="lines",
                line=dict(color=BRAND["muted"], dash="dash", width=1),
                showlegend=False,
                hoverinfo="skip",
            ))
            fig.update_layout(
                xaxis_title="Human Score",
                yaxis_title="Judge Score",
                height=400,
                showlegend=False,
            )
            fig = apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

        with col_bland:
            st.markdown("#### Bland-Altman Agreement Plot")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=means,
                y=diffs,
                mode="markers",
                marker=dict(
                    size=10,
                    color=BRAND["secondary"],
                    line=dict(width=1, color=BRAND["text"]),
                    opacity=0.8,
                ),
                text=cal_df["scenario_name"],
                hovertemplate="<b>%{text}</b><br>Mean: %{x:.0f}<br>Diff: %{y:+.1f}<extra></extra>",
            ))
            # Bias line
            fig.add_hline(y=bias, line=dict(color=BRAND["warning"], dash="dash", width=1.5),
                          annotation_text=f"Bias: {bias:+.1f}", annotation_font_color=BRAND["warning"])
            # Limits of agreement
            fig.add_hline(y=upper_loa, line=dict(color=BRAND["danger"], dash="dot", width=1),
                          annotation_text=f"Upper LoA: {upper_loa:+.1f}", annotation_font_color=BRAND["danger"])
            fig.add_hline(y=lower_loa, line=dict(color=BRAND["danger"], dash="dot", width=1),
                          annotation_text=f"Lower LoA: {lower_loa:+.1f}", annotation_font_color=BRAND["danger"])
            fig.add_hline(y=0, line=dict(color=BRAND["muted"], width=0.5))
            fig.update_layout(
                xaxis_title="Mean of Human & Judge",
                yaxis_title="Difference (Judge − Human)",
                height=400,
                showlegend=False,
            )
            fig = apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

        # ── Failure point overlap ─────────────────────────────────────────
        st.markdown("#### Failure Point Agreement")
        fp_cols = st.columns(3)
        fp_metrics = [
            ("Precision", fp_precision, "% of judge-flagged failures also flagged by human"),
            ("Recall", fp_recall, "% of human-flagged failures also flagged by judge"),
            ("Jaccard Index", fp_jaccard, "Overlap similarity of failure turn sets"),
        ]
        for col, (label, val, desc) in zip(fp_cols, fp_metrics):
            display = f"{val:.0%}" if val is not None else "N/A"
            color = BRAND["accent"] if val and val >= 0.7 else (BRAND["warning"] if val and val >= 0.4 else BRAND["danger"])
            col.markdown(
                f"""<div class="metric-card">
                    <div class="label">{desc}</div>
                    <div class="value" style="color:{color};">{display}</div>
                    <div class="label">{label}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        # ── Per-scenario breakdown ────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Agreement by Scenario")
        scenario_stats = (
            cal_df.groupby("scenario_name")
            .agg(
                n=("human_score", "count"),
                mae=("score_delta", lambda x: np.mean(np.abs(x))),
                mean_human=("human_score", "mean"),
                mean_judge=("judge_score", "mean"),
            )
            .reset_index()
        )
        scenario_stats.columns = ["Scenario", "N", "MAE", "Avg Human", "Avg Judge"]
        scenario_stats = scenario_stats.round(1)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=scenario_stats["Scenario"],
            y=scenario_stats["Avg Human"],
            name="Human",
            marker_color=BRAND["primary"],
            opacity=0.8,
        ))
        fig.add_trace(go.Bar(
            x=scenario_stats["Scenario"],
            y=scenario_stats["Avg Judge"],
            name="Judge",
            marker_color=BRAND["secondary"],
            opacity=0.8,
        ))
        fig.update_layout(
            barmode="group",
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_title="Average Score",
        )
        fig = apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        # ── Calibration note ──────────────────────────────────────────────
        st.info(
            "⚠️ **Note:** The current calibration data uses illustrative placeholder human scores. "
            "For authentic calibration, run `python calibration/harness.py` to hand-score transcripts, "
            "then revisit this dashboard to see real agreement metrics."
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: RUN A TEST
# ══════════════════════════════════════════════════════════════════════════════

with tab_run:
    st.markdown("### Run a Test")
    st.markdown(
        f'<p style="color:{BRAND["muted"]}; margin-top:-8px;">'
        "Paste an agent system prompt, pick a scenario, and watch the conversation unfold. "
        "Requires Ollama running locally.</p>",
        unsafe_allow_html=True,
    )

    # Check Ollama availability
    ollama_available = False
    try:
        from simulator.agent_simulator import is_ollama_available
        ollama_available = is_ollama_available()
    except Exception:
        pass

    if not ollama_available:
        st.warning(
            "🔌 **Ollama not detected.** Live test generation requires Ollama running locally with a model pulled. "
            "Browse the **Test History** tab to explore pre-generated results, or start Ollama and refresh."
        )

    col_prompt, col_scenario = st.columns([2, 1])

    with col_prompt:
        agent_prompt = st.text_area(
            "Agent System Prompt",
            value="""You are a professional AI sales representative for TechFlow, a B2B SaaS platform.
Be helpful, professional, and empathetic. Answer questions directly.
Pricing: Starter $29/seat/mo, Professional $79/seat/mo, Enterprise $149/seat/mo.
Key differentiators: real-time analytics, native Salesforce/HubSpot integration, SOC 2 Type II.
Never trash-talk competitors. Keep responses concise.""",
            height=200,
        )

    with col_scenario:
        scenarios = fetch_scenarios()
        scenario_names = [s["scenario_name"] for s in scenarios]
        selected_scenario = st.selectbox("Scenario", scenario_names)
        run_all = st.checkbox("Run all 6 scenarios", value=False)
        st.markdown(f'<br><p style="color:{BRAND["muted"]}; font-size:13px;">Selected scenario difficulty and personality will determine the caller behavior.</p>', unsafe_allow_html=True)

    if st.button("▶️ Run Simulation", type="primary", disabled=not ollama_available, use_container_width=True):
        if not agent_prompt.strip():
            st.error("Please enter an agent system prompt.")
        else:
            try:
                from simulator.agent_simulator import run_simulation_sync
                from simulator.judge import evaluate_with_consistency_sync
                from simulator.scenarios import SCENARIOS, get_scenario_by_name

                scenarios_to_run = SCENARIOS if run_all else [get_scenario_by_name(selected_scenario)]
                scenarios_to_run = [s for s in scenarios_to_run if s is not None]

                for scenario in scenarios_to_run:
                    st.markdown(f"---\n#### 🎭 {scenario.scenario_name} ({scenario.difficulty_level})")

                    # Run simulation
                    with st.spinner(f"Simulating conversation for {scenario.scenario_name}..."):
                        result = run_simulation_sync(agent_prompt, scenario)

                    transcript = result["transcript"]
                    st.markdown(f"**Conversation** ({result['total_turns']} turns, "
                                f"{'✅ Goal achieved' if result['goal_completed'] else '❌ Goal not achieved'})")

                    # Display transcript
                    for turn in transcript:
                        role_class = "turn-agent" if turn["role"] == "agent" else "turn-caller"
                        role_label = "🤖 AGENT" if turn["role"] == "agent" else "📞 CALLER"
                        st.markdown(
                            f'<div class="{role_class}">'
                            f'<div class="turn-label" style="color:{BRAND["primary"] if turn["role"] == "agent" else BRAND["secondary"]};">'
                            f'Turn {turn["turn"]} — {role_label}</div>'
                            f'{turn["content"]}</div>',
                            unsafe_allow_html=True,
                        )

                    # Run judge with consistency
                    with st.spinner("Evaluating with self-consistency check (3 runs)..."):
                        evaluation = evaluate_with_consistency_sync(transcript, scenario.scenario_description)

                    # Display results
                    st.markdown("#### Evaluation Results")

                    # Overall score badge
                    overall = evaluation["overall_score"]
                    st.markdown(score_badge(overall, "Overall Score"), unsafe_allow_html=True)

                    # Radar chart
                    dimensions = ["response_relevance", "objection_handling", "conversation_flow", "empathy", "goal_completion"]
                    dim_labels = ["Response\nRelevance", "Objection\nHandling", "Conversation\nFlow", "Empathy", "Goal\nCompletion"]
                    values = [evaluation.get(d, 0) for d in dimensions]

                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],
                        theta=dim_labels + [dim_labels[0]],
                        fill="toself",
                        fillcolor=f"{BRAND['primary']}30",
                        line=dict(color=BRAND["primary"], width=2),
                    ))
                    fig.update_layout(
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.1)"),
                            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                        ),
                        height=350,
                        showlegend=False,
                    )
                    fig = apply_theme(fig)
                    st.plotly_chart(fig, use_container_width=True)

                    # Consistency flags
                    if "consistency" in evaluation:
                        st.markdown("**Self-Consistency Check:**")
                        for dim, info in evaluation["consistency"].items():
                            badge_class = "badge-success" if info["confidence"] == "high" else "badge-danger"
                            st.markdown(
                                f'<span class="badge {badge_class}">{dim}: σ={info["stdev"]:.1f} ({info["confidence"]})</span> ',
                                unsafe_allow_html=True,
                            )

                    # Failure points
                    if evaluation.get("failure_points"):
                        st.markdown("**Failure Points:**")
                        for fp in evaluation["failure_points"]:
                            st.markdown(f'- **Turn {fp["turn"]}:** {fp["reason"]}')

                    # Recommendations
                    if evaluation.get("recommendations"):
                        st.markdown("**Recommendations:**")
                        for rec in evaluation["recommendations"]:
                            st.markdown(f"- {rec}")

                    # Save to database
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    scores_breakdown = {d: evaluation.get(d, 0) for d in dimensions}
                    cursor.execute(
                        """INSERT INTO test_runs
                           (scenario_id, agent_system_prompt, conversation_transcript,
                            total_turns, goal_completed, overall_score, scores_breakdown,
                            failure_points, recommendations)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            scenario.id,
                            agent_prompt,
                            json.dumps(transcript),
                            result["total_turns"],
                            1 if result["goal_completed"] else 0,
                            overall,
                            json.dumps(scores_breakdown),
                            json.dumps(evaluation.get("failure_points", [])),
                            "\n".join(evaluation.get("recommendations", [])),
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Results saved to database.")

            except Exception as e:
                logger.exception("Error during simulation")
                st.error(f"Error: {e}")

    # ── Show a seeded example if Ollama unavailable ───────────────────────
    if not ollama_available:
        st.markdown("---")
        st.markdown("#### 📋 Example Result (from seeded data)")
        example = fetch_run_detail(1)
        if example:
            _render_run_detail(example) if False else None  # rendered below in history tab function


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: TEST HISTORY
# ══════════════════════════════════════════════════════════════════════════════

with tab_history:
    st.markdown("### Test History")
    st.markdown(
        f'<p style="color:{BRAND["muted"]}; margin-top:-8px;">'
        "Browse all past test runs. Click a row to see full details.</p>",
        unsafe_allow_html=True,
    )

    runs_df = fetch_all_runs()

    if runs_df.empty:
        st.info("No test runs yet. Seed the database or run a test.")
    else:
        # ── Summary stats ─────────────────────────────────────────────────
        stat_cols = st.columns(4)
        stat_cols[0].metric("Total Runs", len(runs_df))
        stat_cols[1].metric("Avg Score", f"{runs_df['overall_score'].mean():.1f}")
        goal_rate = runs_df["goal_completed"].mean() * 100
        stat_cols[2].metric("Goal Completion", f"{goal_rate:.0f}%")
        stat_cols[3].metric("Scenarios Covered", runs_df["scenario_name"].nunique())

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Score over time trend ─────────────────────────────────────────
        st.markdown("#### Score Trend Over Time")
        trend_df = runs_df.copy()
        trend_df["created_at"] = pd.to_datetime(trend_df["created_at"])
        trend_df = trend_df.sort_values("created_at")

        fig = go.Figure()
        for scenario_name in trend_df["scenario_name"].unique():
            sdf = trend_df[trend_df["scenario_name"] == scenario_name]
            fig.add_trace(go.Scatter(
                x=sdf["created_at"],
                y=sdf["overall_score"],
                mode="lines+markers",
                name=scenario_name,
                marker=dict(size=8),
                line=dict(width=2),
            ))
        fig.add_hline(y=80, line=dict(color=BRAND["accent"], dash="dot", width=1),
                      annotation_text="Good (80)", annotation_font_color=BRAND["accent"])
        fig.add_hline(y=60, line=dict(color=BRAND["warning"], dash="dot", width=1),
                      annotation_text="Adequate (60)", annotation_font_color=BRAND["warning"])
        fig.update_layout(
            height=350,
            xaxis_title="Date",
            yaxis_title="Overall Score",
            yaxis=dict(range=[0, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        )
        fig = apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        # ── Runs table ────────────────────────────────────────────────────
        st.markdown("#### All Runs")

        display_df = runs_df[["id", "scenario_name", "difficulty_level", "overall_score",
                              "goal_completed", "total_turns", "created_at"]].copy()
        display_df.columns = ["ID", "Scenario", "Difficulty", "Score", "Goal Met", "Turns", "Date"]
        display_df["Goal Met"] = display_df["Goal Met"].map({1: "✅", 0: "❌"})
        display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d %H:%M")

        # Score formatting
        def color_score(val):
            try:
                v = float(val)
                if v >= 80:
                    return f"color: {BRAND['accent']}"
                elif v >= 60:
                    return f"color: {BRAND['warning']}"
                return f"color: {BRAND['danger']}"
            except (ValueError, TypeError):
                return ""

        styled = display_df.style.applymap(color_score, subset=["Score"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── Detail view ───────────────────────────────────────────────────
        st.markdown("#### Run Detail")
        selected_id = st.selectbox("Select a run to inspect", display_df["ID"].tolist(), index=0)

        if selected_id:
            detail = fetch_run_detail(selected_id)
            if detail:
                # Header
                score = detail["overall_score"]
                goal = "✅ Goal Achieved" if detail["goal_completed"] else "❌ Goal Not Achieved"
                st.markdown(
                    f'<div style="display:flex; gap:16px; align-items:center; flex-wrap:wrap;">'
                    f'{score_badge(score, "Overall")}'
                    f'<div style="padding:8px 16px;">'
                    f'<div style="font-size:14px; color:{BRAND["muted"]};">{detail["scenario_name"]} · {detail["difficulty_level"]}</div>'
                    f'<div style="font-size:16px; margin-top:4px;">{goal} · {detail["total_turns"]} turns</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)

                col_radar, col_scores = st.columns([1, 1])

                # Radar chart
                with col_radar:
                    try:
                        scores_data = json.loads(detail["scores_breakdown"])
                    except (json.JSONDecodeError, TypeError):
                        scores_data = {}

                    dimensions = ["response_relevance", "objection_handling", "conversation_flow", "empathy", "goal_completion"]
                    dim_labels = ["Response\nRelevance", "Objection\nHandling", "Conversation\nFlow", "Empathy", "Goal\nCompletion"]
                    values = [scores_data.get(d, 0) for d in dimensions]

                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],
                        theta=dim_labels + [dim_labels[0]],
                        fill="toself",
                        fillcolor=f"{BRAND['primary']}30",
                        line=dict(color=BRAND["primary"], width=2),
                        marker=dict(size=6, color=BRAND["primary"]),
                    ))
                    fig.update_layout(
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.1)", tickfont=dict(size=10)),
                            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                        ),
                        height=350,
                        showlegend=False,
                        title=dict(text="Dimension Scores", font=dict(size=14)),
                    )
                    fig = apply_theme(fig)
                    st.plotly_chart(fig, use_container_width=True)

                # Per-dimension scores
                with col_scores:
                    st.markdown("**Per-Dimension Scores:**")
                    for dim, label in zip(dimensions, ["Response Relevance", "Objection Handling", "Conversation Flow", "Empathy", "Goal Completion"]):
                        val = scores_data.get(dim, 0)
                        color = score_color(val)
                        bar_width = max(val, 2)
                        st.markdown(
                            f'<div style="margin:8px 0;">'
                            f'<div style="display:flex; justify-content:space-between; margin-bottom:2px;">'
                            f'<span style="font-size:13px;">{label}</span>'
                            f'<span style="font-size:13px; font-weight:600; color:{color};">{val}</span>'
                            f'</div>'
                            f'<div style="background:rgba(255,255,255,0.06); border-radius:4px; height:8px;">'
                            f'<div style="background:{color}; width:{bar_width}%; height:100%; border-radius:4px; '
                            f'transition: width 0.5s ease;"></div>'
                            f'</div></div>',
                            unsafe_allow_html=True,
                        )

                # Transcript with failure highlighting
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Conversation Transcript:**")

                try:
                    transcript = json.loads(detail["conversation_transcript"])
                    failure_points = json.loads(detail["failure_points"]) if detail["failure_points"] else []
                except (json.JSONDecodeError, TypeError):
                    transcript = []
                    failure_points = []

                failure_turns = set()
                failure_reasons = {}
                for fp in failure_points:
                    if isinstance(fp, dict):
                        failure_turns.add(fp.get("turn", -1))
                        failure_reasons[fp.get("turn", -1)] = fp.get("reason", "")

                for turn_data in transcript:
                    turn_num = turn_data.get("turn", 0)
                    role = turn_data.get("role", "unknown")
                    content = turn_data.get("content", "")
                    is_failure = turn_num in failure_turns

                    role_class = "turn-agent" if role == "agent" else "turn-caller"
                    role_label = "🤖 AGENT" if role == "agent" else "📞 CALLER"
                    role_color = BRAND["primary"] if role == "agent" else BRAND["secondary"]

                    extra_class = " turn-failure" if is_failure else ""
                    failure_note = ""
                    if is_failure and turn_num in failure_reasons:
                        failure_note = (
                            f'<div style="margin-top:8px; padding:8px 12px; background:{BRAND["danger"]}20; '
                            f'border-radius:6px; font-size:12px; color:{BRAND["danger"]};">'
                            f'⚠️ <b>Failure:</b> {failure_reasons[turn_num]}</div>'
                        )

                    st.markdown(
                        f'<div class="{role_class}{extra_class}">'
                        f'<div class="turn-label" style="color:{role_color};">'
                        f'Turn {turn_num} — {role_label}</div>'
                        f'{content}{failure_note}</div>',
                        unsafe_allow_html=True,
                    )

                # Recommendations
                if detail.get("recommendations"):
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("**📝 Recommendations:**")
                    for rec in detail["recommendations"].split("\n"):
                        if rec.strip():
                            st.markdown(f"- {rec.strip()}")

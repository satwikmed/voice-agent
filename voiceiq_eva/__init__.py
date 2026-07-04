"""
VoiceIQ EVA — Pre-launch QA for Retell AI voice agents on EVA-Bench scenarios.

Runs Retell-style agent prompts against standardized enterprise scenarios from
ServiceNow's EVA-Bench (Hugging Face: ServiceNow-AI/eva-bench) and scores
conversations with EVA-A (accuracy) and EVA-X (experience) metrics.
"""

from voiceiq_eva.loader import EvaScenario, load_eva_scenarios
from voiceiq_eva.mapper import eva_record_to_scenario
from voiceiq_eva.scorer import EvaScores, score_eva_run

__all__ = [
    "EvaScenario",
    "load_eva_scenarios",
    "eva_record_to_scenario",
    "EvaScores",
    "score_eva_run",
]

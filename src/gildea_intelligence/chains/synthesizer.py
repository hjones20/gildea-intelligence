"""Synthesizer — cross-claim synthesis with mental model application."""

from __future__ import annotations

import json

from ..llm import call
from ..scratchpad import Scratchpad

MENTAL_MODEL_DESCRIPTIONS = {
    "second_order_thinking": "SECOND-ORDER THINKING: What happens after the obvious outcome? What downstream consequences are most analysts missing?",
    "inversion": "INVERSION: What would have to be true for this thesis to be wrong? Steelman the strongest counter-argument.",
    "incentives": "INCENTIVES: Who benefits from each outcome? How do actor incentives shape the trajectory?",
    "feedback_loops": "FEEDBACK LOOPS: Are there self-reinforcing dynamics that accelerate or dampen the predicted outcome?",
    "inertia": "INERTIA: What existing forces resist the predicted change? How strong are they?",
    "bottlenecks": "BOTTLENECKS: What constraints limit the predicted outcome? Are they loosening or tightening?",
    "critical_mass": "CRITICAL MASS: Is there a tipping point? How close are we? What triggers it?",
    "red_queen": "RED QUEEN EFFECT: Must all actors accelerate just to maintain position? Who falls behind first?",
}

SYNTHESIZER_PROMPT = """\
You are the senior analyst writing the synthesis and recommendations sections of a thesis validation report.

You receive:
1. The original thesis
2. An event timeline showing how the narrative developed
3. Per-claim analyses with evidence assessments and consensus counts
4. A set of mental models to apply as analytical lenses

Your job is to write three sections:

## Synthesis
Integrate across all claims and the timeline. Address:
- Which claims have strong consensus? Which are contested?
- How does the event timeline corroborate or complicate the claim-level evidence?
- What is the overall verdict on the thesis?
- What are the key uncertainties?

Then apply each mental model lens to the evidence. For each lens, cite specific verified evidence that supports or complicates the insight.

## Recommendations
- If you hold this thesis, what should you watch for?
- What would change the verdict?
- What are the second-order implications?

## Executive Summary
Write this LAST, after synthesis and recommendations:
- Overall verdict with confidence level (High / Moderate / Low)
- One-line per claim with consensus strength
- Key risk to the thesis
- 2-3 sentence bottom line

Rules:
- Every claim must cite specific named sources
- Label your interpretations explicitly ("This suggests...", "We interpret this as...")
- Do NOT present inference as sourced fact
- Be specific about consensus counts ("5 sources support, 2 contradict" not "multiple sources agree")
- The executive summary goes at the TOP of the report but is written last using all context
"""


def synthesize(
    thesis: str,
    timeline: str,
    claim_analyses: list[dict],
    mental_models: list[str],
    scratchpad: Scratchpad,
) -> dict:
    """Synthesize across all claims, timeline, and mental models.

    Returns dict with 'executive_summary', 'synthesis', and 'recommendations'.
    """
    # Format claim analyses for the prompt
    claims_text = ""
    for ca in claim_analyses:
        claims_text += f"\n### Claim: {ca['claim']}\n"
        claims_text += f"Assessment: {ca['assessment']} "
        claims_text += f"(Support: {ca.get('support_count', 0)}, "
        claims_text += f"Contradict: {ca.get('contradict_count', 0)})\n"
        claims_text += f"\n{ca.get('narrative', '')}\n"

    # Format mental models
    models_text = "\n".join(
        f"- {MENTAL_MODEL_DESCRIPTIONS.get(m, m)}"
        for m in mental_models
    )

    prompt = f"""THESIS: {thesis}

## Event Timeline
{timeline}

## Claim-by-Claim Analysis
{claims_text}

## Mental Models to Apply
{models_text}

Write the Synthesis, Recommendations, and Executive Summary sections now."""

    raw = call(prompt, system=SYNTHESIZER_PROMPT, max_tokens=4096)
    scratchpad.log("synthesizer", output_length=len(raw))

    return {
        "executive_summary": _extract_section(raw, "Executive Summary"),
        "synthesis": _extract_section(raw, "Synthesis"),
        "recommendations": _extract_section(raw, "Recommendations"),
        "raw": raw,
    }


def _extract_section(text: str, heading: str) -> str:
    """Extract a markdown section by heading."""
    import re
    pattern = rf"##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

"""Orchestrator — decomposes a thesis into testable claims and selects mental models."""

from __future__ import annotations

import json
import re

from .llm import call
from .scratchpad import Scratchpad

ORCHESTRATOR_PROMPT = """\
You are an analytical research planner. Your job is to decompose an investment or market thesis into testable claims and select relevant mental models.

Given a thesis, return a JSON object with:
1. "claims" — a list of 4-6 specific, testable claims that the thesis depends on. Each claim should be independently verifiable against expert sources.
2. "mental_models" — a list of 2-4 mental models from the following set that are most relevant to analyzing this thesis:
   - "second_order_thinking" — What happens after the obvious outcome?
   - "inversion" — What would disprove this thesis?
   - "incentives" — Who benefits from each outcome?
   - "feedback_loops" — Are there self-reinforcing dynamics?
   - "inertia" — What existing forces resist the predicted change?
   - "bottlenecks" — What constraints limit the predicted outcome?
   - "critical_mass" — Is there a tipping point?
   - "red_queen" — Must all actors accelerate to maintain position?

Always include "second_order_thinking", "inversion", and "incentives". Add others only if clearly relevant.

Return ONLY valid JSON, no other text.

Example:
{
  "claims": [
    "Claim 1 text",
    "Claim 2 text"
  ],
  "mental_models": ["second_order_thinking", "inversion", "incentives", "feedback_loops"]
}
"""


def decompose_thesis(thesis: str, scratchpad: Scratchpad) -> dict:
    """Decompose a thesis into testable claims and selected mental models.

    Returns dict with 'claims' (list[str]) and 'mental_models' (list[str]).
    """
    prompt = f"Thesis: {thesis}"
    raw = call(prompt, system=ORCHESTRATOR_PROMPT)
    scratchpad.log("orchestrator", input=thesis, raw_output=raw)

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if json_match:
        raw = json_match.group(1)

    result = json.loads(raw.strip())
    scratchpad.log(
        "orchestrator_parsed",
        claims=result["claims"],
        mental_models=result["mental_models"],
    )
    return result

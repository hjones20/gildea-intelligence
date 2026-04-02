"""Evaluator — quality gate with refinement loop."""

from __future__ import annotations

import json
import re

from .llm import call
from .scratchpad import Scratchpad

EVALUATOR_PROMPT = """\
You are a quality evaluator for thesis validation reports. Score the report against these criteria and identify specific sections that need improvement.

Return a JSON object:
{
  "criteria": [
    {"name": "evidence_traceability", "pass": true/false, "note": "brief explanation"},
    {"name": "consensus_counts_specific", "pass": true/false, "note": ""},
    {"name": "counter_evidence_present", "pass": true/false, "note": ""},
    {"name": "timeline_present_and_ordered", "pass": true/false, "note": ""},
    {"name": "events_paired_with_analysis", "pass": true/false, "note": ""},
    {"name": "synthesis_references_timeline", "pass": true/false, "note": ""},
    {"name": "synthesis_beyond_restating", "pass": true/false, "note": ""},
    {"name": "confidence_calibrated", "pass": true/false, "note": ""},
    {"name": "no_unsupported_inferences", "pass": true/false, "note": ""},
    {"name": "pyramid_structure", "pass": true/false, "note": ""}
  ],
  "passed": <count of passing criteria>,
  "failed": <count of failing criteria>,
  "flagged_sections": ["list of specific sections that need work"],
  "feedback": "Specific, actionable feedback for improving the flagged sections. Be precise about what's wrong and what would fix it."
}

Criteria details:
- evidence_traceability: Every claim traces back to a specific named source
- consensus_counts_specific: Counts cite specific named sources, not "multiple sources"
- counter_evidence_present: Contradicting evidence shown where it exists
- timeline_present_and_ordered: Event timeline with dates, chronologically ordered
- events_paired_with_analysis: Events paired with expert reactions where available
- synthesis_references_timeline: Synthesis integrates timeline narrative, not just claims
- synthesis_beyond_restating: Synthesis identifies non-obvious implications via mental models
- confidence_calibrated: Confidence level matches evidence strength
- no_unsupported_inferences: Inferences are labeled, not presented as sourced facts
- pyramid_structure: Answer first (executive summary), then evidence

Return ONLY valid JSON.
"""


def evaluate_report(report: str, thesis: str, scratchpad: Scratchpad) -> dict:
    """Evaluate a report against quality criteria.

    Returns dict with criteria results, pass/fail counts, and feedback.
    """
    prompt = f"THESIS: {thesis}\n\nREPORT:\n{report}"
    raw = call(prompt, system=EVALUATOR_PROMPT, max_tokens=2048)

    json_match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if json_match:
        raw = json_match.group(1)

    result = json.loads(raw.strip())

    scratchpad.log_evaluation(
        criteria_passed=result.get("passed", 0),
        criteria_failed=result.get("failed", 0),
        flagged=result.get("flagged_sections", []),
    )

    return result


def needs_refinement(evaluation: dict, min_pass: int = 8) -> bool:
    """Check if the report needs another refinement pass."""
    return evaluation.get("passed", 0) < min_pass


REFINER_PROMPT = """\
You are refining a thesis validation report based on specific quality feedback.

You will receive:
1. The current report
2. Specific feedback about what needs improvement
3. The original thesis and evidence

Rewrite ONLY the sections that were flagged. Keep everything else unchanged.
Return the complete updated report.
"""


def refine_report(
    report: str,
    feedback: str,
    thesis: str,
    scratchpad: Scratchpad,
    iteration: int,
) -> str:
    """Refine specific sections of the report based on evaluator feedback."""
    prompt = f"""THESIS: {thesis}

CURRENT REPORT:
{report}

FEEDBACK (fix these issues):
{feedback}

Rewrite the report with these issues fixed. Return the complete updated report."""

    refined = call(prompt, system=REFINER_PROMPT, max_tokens=4096)
    scratchpad.log("refinement", iteration=iteration, feedback_length=len(feedback))
    return refined

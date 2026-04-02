"""Analyzer — per-claim evidence analysis using retrieved evidence."""

from __future__ import annotations

import json

from ..llm import call
from ..scratchpad import Scratchpad

ANALYZER_PROMPT = """\
You are an evidence analyst for a thesis validation report. You receive a claim and retrieved evidence from verified expert sources.

Your job is to:
1. Categorize each piece of evidence as SUPPORTS, CONTRADICTS, or NEUTRAL relative to the claim
2. Count unique sources per position
3. Write a concise analysis section

Return a JSON object with:
{
  "assessment": "SUPPORTED" | "CONTESTED" | "INSUFFICIENT" | "CONTRADICTED",
  "support_count": <number of unique sources supporting>,
  "contradict_count": <number of unique sources contradicting>,
  "supporting_evidence": [
    {"text": "verified claim text", "source": "domain.com", "signal_title": "title"}
  ],
  "contradicting_evidence": [
    {"text": "verified claim text", "source": "domain.com", "signal_title": "title"}
  ],
  "narrative": "2-3 paragraph analysis of the evidence for and against this claim, citing specific sources by name. Be specific about consensus strength."
}

Rules:
- Only count genuinely independent sources (different registrable domains)
- SUPPORTED = 3+ sources support, fewer than 2 contradict
- CONTESTED = significant evidence on both sides (2+ each)
- INSUFFICIENT = fewer than 3 total relevant sources
- CONTRADICTED = 3+ sources contradict, fewer than 2 support
- The narrative should cite specific source names and dates
- Do NOT present inference as sourced fact — label your interpretations

Return ONLY valid JSON.
"""


def analyze_claim(claim_evidence: dict, scratchpad: Scratchpad) -> dict:
    """Analyze evidence for a single claim.

    Takes the output of retriever.retrieve_evidence() and produces an assessment.
    Returns dict with assessment, counts, evidence lists, and narrative.
    """
    claim = claim_evidence["claim"]
    evidence_text = json.dumps(
        {
            "claim": claim,
            "search_results": claim_evidence["search_results"][:10],
            "consensus": claim_evidence["consensus"],
        },
        indent=2,
        default=str,
    )

    prompt = f"CLAIM: {claim}\n\nEVIDENCE:\n{evidence_text}"
    raw = call(prompt, system=ANALYZER_PROMPT, max_tokens=2048)

    # Extract JSON
    import re
    json_match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if json_match:
        raw = json_match.group(1)

    result = json.loads(raw.strip())
    result["claim"] = claim

    scratchpad.log(
        "analyzer",
        claim=claim,
        assessment=result["assessment"],
        support_count=result.get("support_count", 0),
        contradict_count=result.get("contradict_count", 0),
    )

    return result

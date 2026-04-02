"""Timeline — builds chronological event + analysis timeline for a thesis."""

from __future__ import annotations

from gildea_sdk import Gildea

from ..llm import call
from ..scratchpad import Scratchpad

TIMELINE_PROMPT = """\
You are building a chronological event timeline for a thesis validation report.

Given the thesis and a list of signals (events and analyses), produce a timeline that:
1. Orders entries chronologically by publication date
2. Pairs events with expert analyses where they relate to the same development
3. Shows how the narrative around this thesis developed over time
4. Uses this format for each entry:

**[DATE] — [SIGNAL TITLE]** (SOURCE)
[Event/Analysis]: One-sentence summary of what happened or what the expert argued.

Group related event+analysis pairs together. Keep each entry to 1-2 sentences.
Only include signals directly relevant to the thesis. Skip tangential results.
"""


def build_timeline(
    thesis: str,
    claims: list[str],
    gildea: Gildea,
    scratchpad: Scratchpad,
) -> str:
    """Build a chronological timeline of events and analyses related to the thesis.

    Returns the formatted timeline as a string.
    """
    # Search for events related to the thesis
    events = gildea.search(query=thesis, unit_type="summary_sentence", limit=15)
    event_hits = events.get("data", [])
    scratchpad.log_api_call(
        "timeline", "search_text_units",
        {"q": thesis, "unit_type": "summary_sentence", "limit": 15},
        len(event_hits),
    )

    # Search for event claims
    event_claims = gildea.search(query=thesis, unit_type="event_claim", limit=15)
    event_claim_hits = event_claims.get("data", [])
    scratchpad.log_api_call(
        "timeline", "search_text_units",
        {"q": thesis, "unit_type": "event_claim", "limit": 15},
        len(event_claim_hits),
    )

    # Search for thesis-level analysis
    analyses = gildea.search(query=thesis, unit_type="thesis_sentence", limit=15)
    analysis_hits = analyses.get("data", [])
    scratchpad.log_api_call(
        "timeline", "search_text_units",
        {"q": thesis, "unit_type": "thesis_sentence", "limit": 15},
        len(analysis_hits),
    )

    # Combine all signals into a flat list for the LLM
    all_signals = []
    for h in event_hits + event_claim_hits:
        all_signals.append({
            "type": "event",
            "text": h["unit"]["text"],
            "source": h["citation"]["registrable_domain"],
            "signal_title": h["citation"]["signal_title"],
            "published_at": h["citation"]["published_at"],
        })
    for h in analysis_hits:
        all_signals.append({
            "type": "analysis",
            "text": h["unit"]["text"],
            "source": h["citation"]["registrable_domain"],
            "signal_title": h["citation"]["signal_title"],
            "published_at": h["citation"]["published_at"],
        })

    # Sort by date
    all_signals.sort(key=lambda x: x["published_at"])

    scratchpad.log("timeline_signals_collected", total=len(all_signals))

    if not all_signals:
        return "*No timeline events found for this thesis.*"

    # Format signals for the LLM
    signals_text = "\n".join(
        f"- [{s['type'].upper()}] {s['published_at'][:10]} | {s['signal_title']} ({s['source']}): {s['text']}"
        for s in all_signals
    )

    prompt = f"THESIS: {thesis}\n\nSIGNALS:\n{signals_text}"
    timeline = call(prompt, system=TIMELINE_PROMPT, max_tokens=2048)
    scratchpad.log("timeline_complete", length=len(timeline))

    return timeline

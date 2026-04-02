"""Retriever — Gildea API search + consensus mapping for a single claim."""

from __future__ import annotations

from gildea_sdk import Gildea

from ..scratchpad import Scratchpad


def retrieve_evidence(
    claim: str,
    gildea: Gildea,
    scratchpad: Scratchpad,
    limit: int = 15,
    consensus_top_k: int = 3,
) -> dict:
    """Retrieve evidence for a single claim via Gildea search + consensus mapping.

    Returns dict with:
        - claim: the original claim text
        - search_results: raw search hits
        - consensus: list of consensus mappings for top hits
    """
    # Step 1: Search for evidence related to this claim
    results = gildea.search(query=claim, limit=limit)
    hits = results.get("data", [])
    scratchpad.log_api_call(
        "retriever", "search_text_units", {"q": claim, "limit": limit}, len(hits)
    )

    # Step 2: For the top hits, find cross-source consensus via similar_to
    consensus_results = []
    for hit in hits[:consensus_top_k]:
        unit_id = hit["unit"]["unit_id"]
        similar = gildea.search(similar_to=unit_id, limit=10)
        similar_hits = similar.get("data", [])
        scratchpad.log_api_call(
            "retriever",
            "search_text_units",
            {"similar_to": unit_id, "limit": 10},
            len(similar_hits),
        )

        # Collect unique sources
        sources = set()
        sources.add(hit["citation"]["registrable_domain"])
        for s in similar_hits:
            sources.add(s["citation"]["registrable_domain"])

        consensus_results.append(
            {
                "anchor_unit": hit["unit"]["text"],
                "anchor_source": hit["citation"]["registrable_domain"],
                "anchor_signal_title": hit["citation"]["signal_title"],
                "anchor_published_at": hit["citation"]["published_at"],
                "similar_count": len(similar_hits),
                "unique_sources": sorted(sources),
                "unique_source_count": len(sources),
                "similar_texts": [
                    {
                        "text": s["unit"]["text"],
                        "source": s["citation"]["registrable_domain"],
                        "signal_title": s["citation"]["signal_title"],
                        "published_at": s["citation"]["published_at"],
                    }
                    for s in similar_hits[:5]
                ],
            }
        )

    scratchpad.log(
        "retriever_complete",
        claim=claim,
        total_hits=len(hits),
        consensus_mappings=len(consensus_results),
    )

    return {
        "claim": claim,
        "search_results": [
            {
                "text": h["unit"]["text"],
                "unit_type": h["unit"]["unit_type"],
                "source": h["citation"]["registrable_domain"],
                "signal_title": h["citation"]["signal_title"],
                "published_at": h["citation"]["published_at"],
            }
            for h in hits
        ],
        "consensus": consensus_results,
    }

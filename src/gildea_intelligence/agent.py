"""Main CLI agent — entry point for gildea-report command."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from gildea_sdk import Gildea

from .orchestrator import decompose_thesis
from .workers.retriever import retrieve_evidence
from .workers.timeline import build_timeline
from .workers.analyzer import analyze_claim
from .chains.synthesizer import synthesize
from .evaluator import evaluate_report, needs_refinement, refine_report
from .output.markdown import assemble_report, write_report
from .scratchpad import Scratchpad


def validate_thesis(thesis: str, output_path: Path | None = None) -> str:
    """Run the full thesis validation pipeline.

    Returns the final report as a string.
    """
    load_dotenv()

    # Initialize clients
    gildea = Gildea()
    scratchpad = Scratchpad()

    print(f"\n{'='*60}")
    print(f"  Gildea Intelligence — Thesis Validation")
    print(f"{'='*60}")
    print(f"\n  Thesis: {thesis}\n")

    # Step 1: Orchestrator — decompose thesis into claims + select mental models
    print("  [1/7] Decomposing thesis into testable claims...")
    plan = decompose_thesis(thesis, scratchpad)
    claims = plan["claims"]
    mental_models = plan["mental_models"]
    print(f"        → {len(claims)} claims, {len(mental_models)} mental models selected")

    # Step 2: Timeline — build chronological event context
    print("  [2/7] Building event timeline...")
    timeline = build_timeline(thesis, claims, gildea, scratchpad)
    print(f"        → Timeline built")

    # Step 3: Parallel retrieval — evidence for each claim
    print(f"  [3/7] Retrieving evidence for {len(claims)} claims...")
    evidence_by_claim = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(retrieve_evidence, claim, gildea, scratchpad)
            for claim in claims
        ]
        for f in futures:
            evidence_by_claim.append(f.result())
    print(f"        → Evidence retrieved for all claims")

    # Step 4: Parallel analysis — assess each claim's evidence
    print(f"  [4/7] Analyzing evidence per claim...")
    claim_analyses = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(analyze_claim, ev, scratchpad)
            for ev in evidence_by_claim
        ]
        for f in futures:
            claim_analyses.append(f.result())
    for ca in claim_analyses:
        print(f"        → {ca['claim'][:60]}... → {ca['assessment']}")

    # Step 5: Synthesis — integrate across claims + timeline + mental models
    print("  [5/7] Synthesizing across all evidence...")
    synthesis_result = synthesize(thesis, timeline, claim_analyses, mental_models, scratchpad)
    print(f"        → Synthesis complete")

    # Step 6: Assemble report
    print("  [6/7] Assembling report...")
    report = assemble_report(
        thesis=thesis,
        executive_summary=synthesis_result["executive_summary"],
        timeline=timeline,
        claim_analyses=claim_analyses,
        synthesis=synthesis_result["synthesis"],
        recommendations=synthesis_result["recommendations"],
    )

    # Step 7: Evaluate + refine
    print("  [7/7] Evaluating report quality...")
    max_iterations = 3
    for iteration in range(1, max_iterations + 1):
        evaluation = evaluate_report(report, thesis, scratchpad)
        passed = evaluation.get("passed", 0)
        failed = evaluation.get("failed", 0)
        print(f"        → Iteration {iteration}: {passed}/{passed + failed} criteria passed")

        if not needs_refinement(evaluation):
            print(f"        → Quality gate passed")
            break

        if iteration < max_iterations:
            print(f"        → Refining flagged sections...")
            report = refine_report(
                report,
                evaluation.get("feedback", ""),
                thesis,
                scratchpad,
                iteration,
            )

    # Write output
    if output_path is None:
        output_path = scratchpad.report_path
    write_report(report, output_path)
    print(f"\n  Report saved to: {output_path}")
    print(f"  Scratchpad log: {scratchpad.session_dir / 'scratchpad.jsonl'}")

    scratchpad.close()
    return report


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: gildea-report /validate \"Your thesis here\"")
        print("       gildea-report /validate \"Your thesis here\" --output path/to/report.md")
        sys.exit(1)

    command = sys.argv[1]
    if command not in ("/validate", "validate"):
        print(f"Unknown command: {command}")
        print("Available: /validate")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("Error: No thesis provided.")
        print('Usage: gildea-report /validate "AI will permanently compress SaaS valuations"')
        sys.exit(1)

    thesis = sys.argv[2]

    output_path = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = Path(sys.argv[idx + 1])

    validate_thesis(thesis, output_path)


if __name__ == "__main__":
    main()

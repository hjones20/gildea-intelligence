# Gildea Intelligence

An AI market intelligence agent that generates sourced, evidence-based thesis validation reports. Powered by [Gildea's](https://gildea.ai) verified intelligence from 500+ expert sources and Claude's analytical reasoning.

## Quick Start

```bash
# Clone and install
git clone https://github.com/hjones20/gildea-intelligence.git
cd gildea-intelligence
pip install -e .

# Set your API keys
export ANTHROPIC_API_KEY=your-anthropic-key    # Get at console.anthropic.com
export GILDEA_API_KEY=gld_your_key_here        # Get at gildea.ai

# Run a thesis validation
gildea-report /validate "AI will permanently compress SaaS valuations"
```

## What It Does

You give it a thesis. It returns a structured report with:

1. **Executive Summary** — overall verdict with confidence level
2. **Event Timeline** — chronological context showing how the narrative developed, with events paired with expert analysis
3. **Claim-by-Claim Analysis** — each claim decomposed with consensus counts (N sources support, M contradict), specific citations, and evidence on both sides
4. **Synthesis** — cross-claim integration with mental model lenses (second-order thinking, inversion, incentives, and more)
5. **Recommendations** — what to watch for, what would change the verdict

## How It Works

A multi-stage pipeline with quality gates:

```
Thesis
  ↓
[Orchestrator] Decompose into testable claims + select mental models
  ↓
[Timeline] Build chronological event + analysis context
  ↓
[Retrievers] Search Gildea for evidence per claim (parallel)
  ↓
[Consensus] For top evidence, find cross-source agreement via vector similarity
  ↓
[Analyzers] Assess each claim: SUPPORTED / CONTESTED / CONTRADICTED (parallel)
  ↓
[Synthesizer] Integrate across claims + timeline + mental models
  ↓
[Evaluator] Score against 10 quality criteria → refine if needed (up to 3 passes)
  ↓
Report (Markdown)
```

## Example Output

```
## Executive Summary

**Verdict: SUPPORTED (Moderate-High Confidence)**

The thesis that AI will permanently compress SaaS valuations finds support
across 5 of 6 testable claims, with 8 independent sources confirming the
core dynamic...

### Claim 1: AI agents are replacing workflows that SaaS products serve
**Assessment:** SUPPORTED (5 sources support, 1 contradicts)
- *a16z* (Mar 2026): "AI Will Eat Application Software"
- *Bessemer* (Mar 2026): "Legacy SaaS Is Dead, But a New Wave Will Thrive"
- *Bloomberg* (Jan 2026): "AI Boom Is Triggering a Loan Meltdown for Software Companies"
...
```

## Mental Models

The synthesizer applies analytical lenses to the evidence — not generic summaries, but structured reasoning:

**Always applied:**
- Second-Order Thinking — what happens after the obvious outcome?
- Inversion — what would disprove this thesis?
- Incentives — who benefits from each outcome?

**Applied when relevant:**
- Feedback Loops, Inertia, Bottlenecks, Critical Mass, Red Queen Effect

## API Keys

You need two API keys:

| Key | What it's for | Where to get it |
|-----|---------------|-----------------|
| `ANTHROPIC_API_KEY` | Claude API calls (inference costs on you) | [console.anthropic.com](https://console.anthropic.com) |
| `GILDEA_API_KEY` | Verified AI market intelligence data | [gildea.ai](https://gildea.ai) |

## Also Available

**Python SDK** — direct access to the Gildea API:
```bash
pip install gildea
```

**MCP Server** — use Gildea tools in Claude, ChatGPT, Cursor, or any MCP client:
```bash
pip install gildea[mcp]
```

See the [SDK documentation](https://docs.gildea.ai) for details.

## License

MIT

---
name: trend-context-ingestion
description: Search fashion trend and context signals with OpenAI web search, then extract grounded free-form signals.
---

# Trend and context ingestion

Run `tools/run_pipeline.py` (live only). It uses the OpenAI Responses API web search
to gather sources, then an LLM extracts free-form fashion signals. There is no offline
sample mode and no controlled-vocabulary tagging.

Requirements:

- Force web search and preserve source URL, title, and collection time. Retry per query; skip a query only after retries are exhausted.
- Extract each signal as a short Korean `display_keyword` plus a free-text `description` — do not force a fixed tag vocabulary.
- Every signal keeps `evidence_source_ids` drawn only from the provided sources (grounding).
- Validate LLM JSON (schema + evidence subset) before using it.
- Never claim real-time dominance, sales uplift, or conversion improvement without evidence.

Outputs:

- `outputs/source_search_results.json`
- `outputs/extracted_signals.json`

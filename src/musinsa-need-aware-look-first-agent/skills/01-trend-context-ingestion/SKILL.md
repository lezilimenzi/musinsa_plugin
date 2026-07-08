---
name: trend-context-ingestion
description: Search or load fashion trend and context signals, then create grounded display keywords and normalized anchors.
---

# Trend and context ingestion

Use `tools/run_pipeline.py --mode sample` for a reproducible run or `--mode live` for OpenAI web search and LLM extraction.

Requirements:

- Preserve source URL, title, publication date when available, and collection time.
- Extract a short user-facing `display_keyword` for every signal.
- Keep raw evidence and source IDs.
- Validate LLM JSON before using it.
- Never claim real-time dominance, sales uplift, or conversion improvement without evidence.

Outputs:

- `outputs/source_search_results.json`
- `outputs/trend_candidates.csv`
- `outputs/context_anchors.json`
- `outputs/extracted_signals.json`
- `outputs/normalized_anchors.json`


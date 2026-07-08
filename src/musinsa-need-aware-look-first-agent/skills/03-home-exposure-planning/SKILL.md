---
name: home-exposure-planning
description: Group signals into emergent themes, rank full-body looks per theme with an LLM, and assemble grounded slots.
---

# Emergent-theme exposure planning

This MVP does not recommend from a user's search query. Categories are not predefined —
they emerge from the extracted signals.

- Group signals into 3–6 emergent themes; the LLM generates each Korean theme label from the data.
- For each theme, rank eligible full-body looks with an LLM zero-shot ranker: only looks in the catalog, only full-body, each with a Korean `display_keyword` and a grounded `reason`.
- Eligibility: verified full-body look, minimum label confidence, and at least one linked product.
- Do not use a global weighted ranking score.
- Assemble slots round-robin across themes: no duplicate look, at most `per_theme_cap` per theme, filling up to `target_slots`.
- Coverage is best-effort: if too few eligible looks exist, produce fewer slots and record the coverage gap. Do not fabricate looks or relax the full-body / grounding gates.

Outputs:

- `outputs/emergent_themes.json`
- `outputs/theme_look_ranking.csv`
- `outputs/category_look_selection.csv`
- `outputs/home_exposure_plan.csv`

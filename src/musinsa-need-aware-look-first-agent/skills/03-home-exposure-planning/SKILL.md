---
name: home-exposure-planning
description: Group signals into emergent themes, rank full-body looks per theme with an LLM, and assemble grounded slots.
---

# Emergent-theme exposure planning

This MVP does not recommend from a user's search query. Categories are not predefined —
they emerge from the extracted signals.

- Group signals into 3–6 emergent themes; the LLM generates each Korean theme label from the data.
- For each theme, rank eligible full-body looks with an LLM zero-shot ranker: only looks in the catalog, only full-body, each with a Korean `display_keyword` and a grounded `reason`.
- Give the ranker each look's brand and its `specialty`/`identity` (from `brand_catalog.csv`). When a brand's specialty strongly matches the theme (e.g. a swimwear-specialist brand for a water/festival theme), the fit score should rise and the reason should cite the brand. Do not raise the score for an unrelated brand.
- Eligibility: verified full-body look, minimum label confidence, and at least one linked product.
- Do not use a global weighted popularity score; ranking is per-theme LLM fit only.
- Assemble slots by global assignment: sort every (theme, look) pair by `fit_score` and take the top pairs so each look lands on its best-fitting theme. No duplicate look, at most `per_theme_cap` per theme, up to `target_slots`.
- Drop any pair below `min_fit_score`; theme balance is not enforced (trends can concentrate in a few themes).
- Coverage is best-effort: if too few pairs clear the floor, produce fewer slots and record the coverage gap. Do not fabricate looks or relax the full-body / grounding gates.

Outputs:

- `outputs/emergent_themes.json`
- `outputs/theme_look_ranking.csv`
- `outputs/home_exposure_plan.csv`

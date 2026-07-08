---
name: home-exposure-planning
description: Allocate category quotas and select keyword-matched full-body looks for home, recommendation, or campaign slots.
---

# Home exposure planning

This MVP does not recommend from a user's search query.

- Allocate two slots each to trend, event, weather/season, item-led, and occasion categories.
- Do not use a global weighted ranking score.
- Require a display keyword, a direct category anchor match, a verified full-body look, minimum label confidence, and at least one linked product.
- Apply deterministic category-specific priority rules.
- Reassign unfilled quotas in the configured fallback order without relaxing quality requirements.

Outputs:

- `outputs/home_exposure_categories.json`
- `outputs/anchor_matched_look_candidates.csv`
- `outputs/category_look_selection.csv`
- `outputs/home_exposure_plan.csv`


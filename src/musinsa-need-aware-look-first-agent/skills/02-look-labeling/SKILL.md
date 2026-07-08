---
name: look-labeling
description: Label sample fashion looks and verify that eligible slot candidates are full-body outfits.
---

# Look labeling

- Prefer existing metadata and linked product attributes.
- Normalize tags with `inputs/synonym_dictionary.yaml`.
- Preserve label source and confidence.
- Treat human-reviewed labels as strongest evidence.
- A core slot candidate must have `shot_type=full_body` or `full_body_visible=true`.
- Do not infer full-body visibility when the input does not provide it.

Outputs:

- `outputs/look_catalog_labeled.csv`
- `outputs/label_confidence_report.csv`


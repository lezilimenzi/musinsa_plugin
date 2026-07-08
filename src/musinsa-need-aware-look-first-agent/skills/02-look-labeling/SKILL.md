---
name: look-labeling
description: Verify full-body looks and compute label confidence from metadata, linked products, and human review.
---

# Look labeling

- Prefer existing metadata and linked product attributes.
- Compute `label_confidence` from label sources, linked-product presence, and human review.
- Treat human-reviewed labels as strongest evidence.
- A core slot candidate must have `shot_type=full_body` or `full_body_visible=true`.
- Do not infer full-body visibility when the input does not provide it.

Outputs:

- `outputs/look_catalog_labeled.csv`
- `outputs/label_confidence_report.csv`

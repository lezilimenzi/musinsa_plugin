---
name: look-labeling
description: Verify full-body looks and compute label confidence from metadata and linked products.
---

# Look labeling

- Prefer existing metadata and linked product attributes.
- Compute `label_confidence` from label sources and linked-product presence.
- A core slot candidate must have `shot_type=full_body` or `full_body_visible=true`.
- Do not infer full-body visibility when the input does not provide it.

Outputs:

- `outputs/look_catalog_labeled.csv`

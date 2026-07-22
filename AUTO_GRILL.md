# Auto-grill record

## Revisions

- Workbook hashing is streamed instead of loading the entire input into memory.
- ZIP entry count, total expanded bytes, compression ratio, duplicate names, encryption, and unsafe member paths are validated before semantic parsing.
- XML and media parts have separate byte limits; DTD/entity declarations are rejected.
- Cell count and drawing context radius are bounded.
- Media extraction uses exclusive creation and destination ancestry checks, preventing silent overwrite or symlink redirection.
- Shared/array formula attributes are retained even when a formula body is absent on a follower cell.
- Exact XML numeric text and explicitly labeled cached formula values are retained; integer parsing no longer round-trips through a precision-losing float.
- Comments, macros, and custom XML are explicitly inventoried as separate/unsupported content.

## Evidence limits

Structural extraction does not recalculate formulas, render Excel layout, evaluate external links, perform OCR, or prove visual reading order. Cached formula values may be stale. Chart source formulas are stronger evidence than pixel interpretation but still depend on workbook state. Unsupported parts and limit failures are coverage gaps.

## Porting decisions

- `PORTING-DECISION-001`: tune compressed/expanded/part/media/cell/context limits to the destination's resource budget.
- `PORTING-DECISION-002`: select and pin a spreadsheet recalculation/rendering engine before treating cached formula values as current.
- `PORTING-DECISION-003`: decide whether filenames, absolute paths, hidden content, comments, external-link targets, formulas, and nearby-cell context may be shared.
- `PORTING-DECISION-004`: approve a strictly local OCR/vision backend and retention policy before interpreting extracted images containing sensitive material.

# Scene model schema

## Top level

| Field | Meaning |
|---|---|
| `schema_version` | Contract version for downstream consumers (currently `1.1`) |
| `parser_version` | Parser implementation version |
| `source` | Source path or redacted filename, redaction flag, byte size, and SHA-256 |
| `summary` | Counts of sheets, cells, merges, objects, and media |
| `sheets` | Ordered worksheet scene records |
| `media` | Deduplicated embedded image manifest |
| `unsupported_or_separate_parts` | Detected OOXML features needing another parser |
| `warnings` | Missing or malformed relationship findings |

## Sheet record

Each sheet contains:

- `name`, `state`, `part`, and used `dimension`;
- typed `cells` with `value`, exact XML `raw_value`, formula text/attributes, explicitly labeled `cached_value`, and style metadata;
- `merged_ranges`;
- row and column sizes/hidden flags;
- `drawing_objects`;
- cells containing `IMAGE()` formulas.

## Drawing object

All drawing objects have:

```json
{
  "id": "drawing1-object-1",
  "kind": "image",
  "anchor": {
    "type": "twoCellAnchor",
    "from": {"cell": "B12", "col": 1, "row": 11},
    "to": {"cell": "J31", "col": 9, "row": 30}
  },
  "context": {
    "cells": [{"ref": "A11", "value": "Wake-up sequence"}],
    "nearest_cells": [{"ref": "B10", "value": "SWR-1204", "distance": 2}],
    "merged_ranges": ["A11:J11"]
  }
}
```

Image objects add media part, format, dimensions, byte size, and SHA-256. Chart objects add chart type, title, and source formulas. Shape objects add extracted DrawingML text.

## Evidence join

Key downstream interpretations by:

```text
source.sha256 + sheet.name + drawing_object.id + media.sha256
```

This prevents collisions across workbook revisions and repeated filenames.

Use `--redact-paths` when Scene JSON may be shared. It stores only filenames in `source.path` and media `extracted_path`; hashes and evidence joins remain unchanged.

`cached_value` is extracted evidence, not a recalculation result. Keep `raw_value` when decimal precision matters and do not claim a cached value is current without a separately identified recalculation engine.

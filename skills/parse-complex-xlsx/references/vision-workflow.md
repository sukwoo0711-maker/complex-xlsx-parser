# OCR and vision workflow

## Gate remote processing

Before sending media to a remote model:

1. Confirm user authorization.
2. Review workbook sensitivity and image alt text/captions.
3. Mask secrets when masking does not destroy the analysis target.
4. Record provider, model, prompt version, image SHA-256, and timestamp.

Use a local OCR or vision backend when remote processing is not authorized.

## Build the prompt packet

Send the image together with bounded workbook context:

```json
{
  "object_id": "drawing1-object-1",
  "sheet": "Startup",
  "anchor": "B12:J31",
  "header_path": ["Power", "Startup"],
  "nearby_cells": [
    {"ref": "A11", "value": "Wake-up sequence"},
    {"ref": "C32", "value": 20},
    {"ref": "D32", "value": "ms"}
  ],
  "requested_schema": "TIMING_DIAGRAM"
}
```

Do not include the entire workbook when nearby evidence is sufficient.

## Validate results

- Require structured output for timing, state, register, and packet diagrams.
- Preserve OCR bounding boxes when the backend provides them.
- Compare image-derived numbers and units with nearby cells.
- Flag disagreement instead of selecting a winner silently.
- Require human review for low-resolution images, ambiguous edges, rotated text, or schematic safety claims.

## Evidence labels

- `EXTRACTED`: directly present in OOXML or media bytes.
- `OCR`: recognized glyph content.
- `VISION-INFERRED`: semantic relationship inferred from pixels.
- `CROSS-CHECKED`: supported by both image and cell evidence.
- `CONFLICT`: image and cell evidence disagree.
- `UNKNOWN`: evidence is insufficient.

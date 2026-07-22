# OCR and vision workflow

## Choose an authorized backend

Before sending media or cell context to any secondary backend:

1. Confirm authority to process the content and whether local, self-hosted, or remote processing is allowed.
2. Review sensitivity, applicable policy and jurisdiction, retention, and image alt text or captions.
3. Minimize the context and mask sensitive data when masking does not destroy the analysis target.
4. Check language, script, writing direction, handwriting, and layout support.
5. Record backend class, product or project and version when known, configuration or prompt version, image SHA-256, and timestamp.

Use an authorized local or self-hosted backend when remote processing is not allowed. If no suitable backend exists, record `NOT_ANALYZED` and the limitation.

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

Do not include the entire workbook when bounded nearby evidence is sufficient. Preserve original-language text; request translation as a separate derived field only when needed.

## Validate results

- Require structured output for timing, state, register, and packet diagrams.
- Preserve OCR bounding boxes when the backend provides them.
- Preserve reading order and language/script metadata when the backend provides them.
- Compare image-derived numbers and units with nearby cells.
- Flag disagreement instead of selecting a winner silently.
- Do not treat agreement among multiple backends as proof when they may share training data or failure modes.
- Require an appropriately qualified review for low-resolution images, ambiguous edges, unsupported languages or layouts, or safety-relevant schematic claims.
- Provide text alternatives for findings conveyed by color, icons, shape, or position.

## Evidence labels

- `EXTRACTED`: directly present in OOXML or media bytes.
- `OCR`: recognized glyph content.
- `VISION-INFERRED`: semantic relationship inferred from pixels.
- `CROSS-CHECKED`: supported by both image and cell evidence.
- `CONFLICT`: image and cell evidence disagree.
- `NOT_ANALYZED`: no authorized or capable backend was available.
- `UNKNOWN`: evidence is insufficient.

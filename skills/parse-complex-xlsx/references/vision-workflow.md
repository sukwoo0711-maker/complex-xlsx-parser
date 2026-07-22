# Offline image-analysis workflow

## Enforce local processing

Before processing media or cell context:

1. Use only software and models whose inference runs on the local machine without a network call.
2. Disable telemetry, automatic uploads, cloud fallback, and remote model discovery when the selected local tool exposes those features.
3. Review sensitivity, retention, and image alt text or captions.
4. Minimize the context and mask sensitive data when masking does not destroy the analysis target.
5. Check language, script, writing direction, handwriting, and layout support.
6. Record backend name and version, local configuration, image SHA-256, and timestamp.

Do not upload data to a hosted API or remote service. If no capable offline backend exists, record `NOT_ANALYZED` and the limitation.

## Build the prompt packet

Provide the local backend with the image and bounded workbook context:

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
- Do not treat agreement among multiple local backends as proof when they may share training data or failure modes.
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

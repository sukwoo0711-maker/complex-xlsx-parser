---
name: parse-complex-xlsx
description: Parse visually complex OOXML workbooks into evidence-linked scene models containing cells, formulas, merged ranges, images, anchors, shapes, charts, and nearby cell context. Use for .xlsx/.xlsm/.xltx/.xltm specifications that mix parallel tables, merged headers, screenshots, diagrams, numeric constraints, charts, or image-based requirements; for extracting media before OCR or vision analysis; and for tracing derived claims back to exact sheets, cells, ranges, and drawing objects.
---

# Parse Complex XLSX

Treat a workbook as a two-dimensional document scene, not a flat table. Preserve source coordinates and uncertainty throughout extraction and interpretation.

## Workflow

1. Fingerprint the workbook and keep the raw file unchanged.
2. Run the bundled wrapper from any working directory:

   ```shell
   python <skill-dir>/scripts/parse_xlsx.py input.xlsx --pretty -o scene.json --extract-media media
   ```

3. Inspect `summary`, `warnings`, and `unsupported_or_separate_parts` before interpreting content.
4. Read [scene-schema.md](references/scene-schema.md) when consuming or extending the JSON.
5. Use cells, merged ranges, and chart references directly. Do not OCR structured cell values.
6. For each drawing object, use its anchor and `context.cells` to establish captions, requirement IDs, units, and nearby constraints.
7. Read [vision-workflow.md](references/vision-workflow.md) before sending extracted media to OCR or a multimodal model.
8. Join OCR/Vision results back by image SHA-256 and object ID. Never join by filename alone.
9. Report claims with sheet, cell/range, object ID, image hash, parser version, and interpretation confidence.

## Interpretation rules

- Keep extracted facts separate from OCR text and semantic inference.
- Prefer cell values over visually repeated text when both describe the same field, but report conflicts.
- Treat merged headers as region context; do not duplicate their text into every cell without marking the derivation.
- Treat charts by their source formulas when available. Use rendered chart vision only for visual annotations not encoded in chart XML.
- Treat `IMAGE()` formulas as linked resources. Do not fetch URLs unless the user authorizes network access and the URL is safe.
- Treat hidden sheets, rows, and columns as content, not deletions.
- Do not send workbook media to remote models unless the user permits it and sensitive content has been considered.
- Mark rich-data cell images, VML drawings, unsupported drawing children, protected/encrypted packages, and external links as coverage gaps.

## Engineering diagram routing

Classify extracted images before semantic analysis:

- `TEXT_SCREENSHOT`: OCR first.
- `TABLE_SCREENSHOT`: table OCR plus row/column reconstruction.
- `TIMING_DIAGRAM`: extract signals, edges, intervals, units, and inequalities.
- `STATE_DIAGRAM`: extract states, transitions, guards, and actions.
- `REGISTER_MAP`: extract bit ranges, access modes, reset values, and field names.
- `PACKET_FORMAT`: extract offsets, widths, byte order, and constraints.
- `SCHEMATIC`: preserve net and component labels; require human review for electrical claims.
- `UI_SCREEN`, `PHOTO`, or `UNKNOWN`: describe conservatively and retain raw evidence.

## Required deliverables

Produce:

1. Workbook inventory and coverage gaps.
2. Scene JSON and extracted media manifest.
3. Object-to-context mapping.
4. Optional OCR/Vision results keyed by image hash.
5. Conflicts between cell data and image-derived statements.
6. Evidence-linked findings with confidence and review status.

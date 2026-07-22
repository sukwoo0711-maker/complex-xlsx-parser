---
name: parse-complex-xlsx
description: Parse structurally or visually complex OOXML workbooks into evidence-linked scene models containing cells, formulas, merged ranges, images, anchors, shapes, charts, and nearby cell context. Use for .xlsx/.xlsm/.xltx/.xltm documents that mix adjacent tables, merged headers, screenshots, diagrams, multilingual text, numeric constraints, charts, or image-based requirements; for accessible and privacy-aware media extraction before OCR or multimodal analysis; and for tracing derived claims back to exact sheets, cells, ranges, and drawing objects without depending on a particular AI provider.
---

# Parse Complex XLSX

Treat a workbook as a two-dimensional document scene, not a flat table. Preserve source coordinates and uncertainty throughout extraction and interpretation.

## Workflow

1. Fingerprint the workbook and keep the raw file unchanged.
2. Run the bundled wrapper from any working directory:

   ```shell
   python <skill-dir>/scripts/parse_xlsx.py input.xlsx --pretty -o scene.json --extract-media media --redact-paths
   ```

3. Inspect `summary`, `warnings`, and `unsupported_or_separate_parts` before interpreting content.
   Omit `--redact-paths` only when downstream local tooling requires absolute paths and the output will remain appropriately protected.
4. Read [scene-schema.md](references/scene-schema.md) when consuming or extending the JSON.
5. Read [inclusive-analysis.md](references/inclusive-analysis.md) when the workbook is multilingual, uses unfamiliar conventions, contains personal data, or will inform decisions about people.
6. Use cells, merged ranges, and chart references directly. Avoid OCR for structured cell values unless validating rendering or resolving an extraction gap.
7. For each drawing object, use its anchor and `context.cells` to establish captions, identifiers, units, and nearby constraints.
8. Read [vision-workflow.md](references/vision-workflow.md) before sending extracted media to any OCR or multimodal backend.
9. Join OCR or multimodal results back by image SHA-256 and object ID. Never join by filename alone.
10. Report claims with source coordinates, evidence class, parser version, uncertainty, and review status. Avoid false precision in confidence scores.

## Interpretation rules

- Keep extracted facts separate from OCR text and semantic inference.
- Preserve original text, Unicode, units, reading order, and locale-specific number/date notation. Put translations and normalized values in separate fields.
- Prefer cell values over visually repeated text when both describe the same field, but report conflicts rather than silently choosing a winner.
- Treat merged headers as region context; do not duplicate their text into every cell without marking the derivation.
- Treat charts by their source formulas when available. Use rendered chart vision only for visual annotations not encoded in chart XML.
- Treat `IMAGE()` formulas as linked resources. Do not fetch URLs unless the user authorizes network access and the URL is safe.
- Treat hidden sheets, rows, and columns as content, not deletions.
- Minimize context sent to any secondary tool. Do not send workbook media or cell context to a remote service without appropriate authorization and a sensitivity, policy, and jurisdiction check.
- Do not infer identity, demographic traits, disability, intent, competence, or protected characteristics from names, language, images, or formatting unless the task legitimately requires it and the evidence supports it.
- Treat accessibility text, captions, and reading order as evidence while recognizing that they may be missing, stale, or incorrect.
- Treat disagreement among tools or reviewers as unresolved evidence; do not use majority vote as a substitute for validation.
- Mark rich-data cell images, VML drawings, unsupported drawing children, protected/encrypted packages, and external links as coverage gaps.

## Engineering diagram routing

Classify extracted images before semantic analysis:

- `TEXT_SCREENSHOT`: OCR with language and writing-direction detection or explicit configuration.
- `TABLE_SCREENSHOT`: table OCR plus row/column and reading-order reconstruction.
- `TIMING_DIAGRAM`: extract signals, edges, intervals, units, and inequalities.
- `STATE_DIAGRAM`: extract states, transitions, guards, and actions.
- `REGISTER_MAP`: extract bit ranges, access modes, reset values, and field names.
- `PACKET_FORMAT`: extract offsets, widths, byte order, and constraints.
- `SCHEMATIC`: preserve net and component labels; require a qualified domain review for safety-relevant electrical claims.
- `UI_SCREEN`, `PHOTO`, or `UNKNOWN`: describe conservatively and retain raw evidence.

## Required deliverables

Produce:

1. Workbook inventory and coverage gaps.
2. Scene JSON and extracted media manifest.
3. Object-to-context mapping.
4. Optional OCR/Vision results keyed by image hash.
5. Conflicts between cell data and image-derived statements.
6. Evidence-linked findings with confidence and review status.
7. Language, locale, accessibility, privacy, and tool-coverage limitations that could materially change interpretation.

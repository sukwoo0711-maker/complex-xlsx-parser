# Complex XLSX Parser

A dependency-free OOXML parser that treats a workbook as a two-dimensional document scene rather than a flat table.

It extracts:

- typed cells, formulas, and number-format metadata;
- merged ranges and row/column layout;
- images with original media, hashes, dimensions, and one/two-cell anchors;
- charts with types and source-range formulas;
- drawing shapes and text;
- nearby cell and merge context for each drawing object;
- `IMAGE()` formula locations and advanced parts requiring separate handling.

## Usage

```shell
python -m complex_xlsx_parser spec.xlsx --pretty -o scene.json --extract-media extracted-media --redact-paths
```

The parser performs no OCR and makes no network calls. Optional OCR and image interpretation must use an offline local backend; the bundled skill instructs the agent to stop rather than use a hosted service.

OOXML input is treated as untrusted. Default limits cover compressed input size, ZIP entry count, total uncompressed size, compression ratio, XML/media part size, cell count, and context radius. Duplicate, encrypted, path-escaping, DTD/entity-bearing, or limit-exceeding packages fail closed. Tune limits only within an explicit memory, storage, and review budget.

The bundled skill is backend-neutral within an offline boundary. It preserves source language and coordinates, treats translations and normalized values as derived data, records uncertainty and coverage gaps, and includes guidance for right-to-left or vertical text, locale-specific values, accessibility metadata, and consequential-use review. Before sharing Scene JSON, review absolute paths, hidden content, comments, metadata, and nearby-cell context for sensitive information.

Use `--redact-paths` for portable or shared output. Omit it only when protected local tooling requires absolute paths.

## Current boundaries

- Legacy binary `.xls` files are out of scope.
- Rich-data in-cell images, VML, slicers, macros, and external links are detected or preserved as gaps but not semantically expanded.
- Comments, custom XML, and macros are inventoried as separate/unsupported parts; their content is not interpreted.
- OCR and vision interpretation are intentionally separate from structural parsing.
- Password-encrypted OOXML packages must be decrypted before parsing.

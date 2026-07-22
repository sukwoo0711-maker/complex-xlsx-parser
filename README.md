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
python -m complex_xlsx_parser spec.xlsx --pretty -o scene.json --extract-media extracted-media
```

The parser performs no OCR and calls no remote service. OCR and multimodal interpretation belong in downstream adapters so sensitive workbooks can remain local.

## Tests

```shell
python -m unittest discover -s tests -v
```

Regression fixtures come from permissively licensed public repositories and are documented in `tests/fixtures/SOURCES.md`.

To refresh them from their pinned upstream URLs and verify SHA-256 hashes:

```shell
python tests/fetch_fixtures.py
```

## Current boundaries

- Legacy binary `.xls` files are out of scope.
- Rich-data in-cell images, VML, slicers, macros, and external links are detected or preserved as gaps but not semantically expanded.
- OCR and vision interpretation are intentionally separate from structural parsing.
- Password-encrypted OOXML packages must be decrypted before parsing.

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .parser import parse_workbook
from .parser import (
    DEFAULT_MAX_CELLS, DEFAULT_MAX_COMPRESSION_RATIO, DEFAULT_MAX_CONTEXT_RADIUS,
    DEFAULT_MAX_INPUT_BYTES, DEFAULT_MAX_MEDIA_BYTES, DEFAULT_MAX_PART_BYTES,
    DEFAULT_MAX_TOTAL_UNCOMPRESSED, DEFAULT_MAX_ZIP_ENTRIES,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a complex XLSX workbook into an evidence-linked scene model."
    )
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--extract-media", type=Path)
    parser.add_argument("--context-radius", type=int, default=2)
    parser.add_argument("--max-input-bytes", type=int, default=DEFAULT_MAX_INPUT_BYTES)
    parser.add_argument("--max-part-bytes", type=int, default=DEFAULT_MAX_PART_BYTES)
    parser.add_argument("--max-media-bytes", type=int, default=DEFAULT_MAX_MEDIA_BYTES)
    parser.add_argument("--max-total-uncompressed", type=int, default=DEFAULT_MAX_TOTAL_UNCOMPRESSED)
    parser.add_argument("--max-zip-entries", type=int, default=DEFAULT_MAX_ZIP_ENTRIES)
    parser.add_argument("--max-compression-ratio", type=float, default=DEFAULT_MAX_COMPRESSION_RATIO)
    parser.add_argument("--max-cells", type=int, default=DEFAULT_MAX_CELLS)
    parser.add_argument("--max-context-radius", type=int, default=DEFAULT_MAX_CONTEXT_RADIUS)
    parser.add_argument(
        "--redact-paths",
        action="store_true",
        help="Store filenames instead of absolute local paths in the scene model.",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        result = parse_workbook(
            args.workbook,
            extract_media=args.extract_media,
            context_radius=args.context_radius,
            redact_paths=args.redact_paths,
            max_input_bytes=args.max_input_bytes,
            max_part_bytes=args.max_part_bytes,
            max_media_bytes=args.max_media_bytes,
            max_total_uncompressed=args.max_total_uncompressed,
            max_zip_entries=args.max_zip_entries,
            max_compression_ratio=args.max_compression_ratio,
            max_cells=args.max_cells,
            max_context_radius=args.max_context_radius,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    text = json.dumps(
        result,
        indent=2 if args.pretty else None,
        ensure_ascii=False,
        sort_keys=False,
    ) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0

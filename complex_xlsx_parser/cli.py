from __future__ import annotations

import argparse
import json
from pathlib import Path

from .parser import parse_workbook


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse a complex XLSX workbook into an evidence-linked scene model."
    )
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--extract-media", type=Path)
    parser.add_argument("--context-radius", type=int, default=2)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        result = parse_workbook(
            args.workbook,
            extract_media=args.extract_media,
            context_radius=max(0, args.context_radius),
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

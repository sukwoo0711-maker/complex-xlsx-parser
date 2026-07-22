#!/usr/bin/env python3
"""Skill entry point for the complex-xlsx-parser package."""

try:
    from complex_xlsx_parser.cli import main
except ImportError as exc:
    raise SystemExit(
        "complex-xlsx-parser is not installed. From the repository root run: "
        "python -m pip install -e ."
    ) from exc

raise SystemExit(main())

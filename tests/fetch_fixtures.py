"""Fetch public regression fixtures and verify their exact hashes."""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path


FIXTURES = {
    "markitdown_xlsx_complex_layout.xlsx": (
        "https://raw.githubusercontent.com/microsoft/markitdown/main/packages/markitdown-ocr/tests/ocr_test_data/xlsx_complex_layout.xlsx",
        "7f333462745b6aacf6862d8e02c3213cf6de1b41b33facde5674321b5f2554c1",
    ),
    "openpyxl_merge_range.xlsx": (
        "https://raw.githubusercontent.com/ericgazoni/openpyxl/master/openpyxl/tests/test_data/genuine/merge_range.xlsx",
        "a60125df30fb4179a4132cb627534695dc2b05214d4b919f83eb47c625b56830",
    ),
    "openpyxl_charts.xlsx": (
        "https://raw.githubusercontent.com/ericgazoni/openpyxl/master/openpyxl/sample/files/charts.xlsx",
        "6f1b80c730af5dcd92a5a9c83b35472855744f99a20052ed7d723bedf363571d",
    ),
}


def main() -> int:
    destination = Path(__file__).parent / "fixtures" / "external"
    destination.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in FIXTURES.items():
        data = urllib.request.urlopen(url, timeout=30).read()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise SystemExit(f"Hash mismatch for {name}: {actual}")
        (destination / name).write_bytes(data)
        print(f"verified {name} {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

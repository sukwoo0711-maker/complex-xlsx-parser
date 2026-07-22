import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from complex_xlsx_parser.parser import parse_workbook


WORKBOOK = '''<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <sheets><sheet name="Spec" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''
WORKBOOK_RELS = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rId1" Type="worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''
SHEET = '''<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
 <dimension ref="A1:A3"/><sheetData>
  <row r="1"><c r="A1" t="inlineStr"><is><t>Hello</t></is></c></row>
  <row r="2"><c r="A2"><v>12345678901234567890</v></c></row>
  <row r="3"><c r="A3"><f t="shared" si="0">A2+1</f><v>12345678901234567891</v></c></row>
 </sheetData>
</worksheet>'''


def make_book(path: Path, extras=None, compression=ZIP_STORED):
    with ZipFile(path, "w", compression=compression) as archive:
        archive.writestr("xl/workbook.xml", WORKBOOK)
        archive.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
        archive.writestr("xl/worksheets/sheet1.xml", SHEET)
        for name, data in extras or []:
            archive.writestr(name, data)


class ParserSafetyTests(unittest.TestCase):
    def test_minimal_workbook_and_redacted_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            make_book(path)
            result = parse_workbook(path, redact_paths=True)
            self.assertEqual(result["sheets"][0]["cells"][0]["value"], "Hello")
            self.assertEqual(result["sheets"][0]["cells"][1]["value"], 12345678901234567890)
            self.assertEqual(result["sheets"][0]["cells"][2]["cached_value"], 12345678901234567891)
            self.assertEqual(result["sheets"][0]["cells"][2]["formula_attributes"]["t"], "shared")
            self.assertEqual(result["source"]["path"], "book.xlsx")
            self.assertEqual(result["parser_version"], "0.3.0")
            self.assertEqual(result["schema_version"], "1.1")

    def test_input_size_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            make_book(path)
            with self.assertRaisesRegex(ValueError, "max_input_bytes"):
                parse_workbook(path, max_input_bytes=10)

    def test_context_radius_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            make_book(path)
            with self.assertRaisesRegex(ValueError, "context_radius"):
                parse_workbook(path, context_radius=101)

    def test_part_size_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            make_book(path)
            with self.assertRaisesRegex(ValueError, "part exceeds byte limit"):
                parse_workbook(path, max_part_bytes=10)

    def test_cell_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            make_book(path)
            with self.assertRaisesRegex(ValueError, "max_cells"):
                parse_workbook(path, max_cells=2)

    def test_zip_entry_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            make_book(path)
            with self.assertRaisesRegex(ValueError, "max_zip_entries"):
                parse_workbook(path, max_zip_entries=2)

    def test_compression_ratio_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            make_book(path, [("xl/large.bin", b"0" * 100_000)], ZIP_DEFLATED)
            with self.assertRaisesRegex(ValueError, "compression ratio"):
                parse_workbook(path, max_compression_ratio=10)

    def test_duplicate_zip_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with ZipFile(path, "w") as archive:
                    archive.writestr("xl/workbook.xml", WORKBOOK)
                    archive.writestr("xl/workbook.xml", WORKBOOK)
            with self.assertRaisesRegex(ValueError, "duplicate ZIP"):
                parse_workbook(path)

    def test_unsafe_zip_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            make_book(path, [("../escape.xml", "x")])
            with self.assertRaisesRegex(ValueError, "Unsafe ZIP entry"):
                parse_workbook(path)

    def test_dtd_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.xlsx"
            malicious = '<!DOCTYPE x [<!ENTITY y "z">]><workbook>&y;</workbook>'
            with ZipFile(path, "w") as archive:
                archive.writestr("xl/workbook.xml", malicious)
            with self.assertRaisesRegex(ValueError, "DTD/entity"):
                parse_workbook(path)


if __name__ == "__main__":
    unittest.main()

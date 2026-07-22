import json
import tempfile
import unittest
from pathlib import Path

from complex_xlsx_parser import parse_workbook


FIXTURES = Path(__file__).parent / "fixtures" / "external"


class ParserTests(unittest.TestCase):
    def test_complex_image_workbook(self):
        path = FIXTURES / "markitdown_xlsx_complex_layout.xlsx"
        with tempfile.TemporaryDirectory() as tmp:
            result = parse_workbook(path, extract_media=tmp, context_radius=1)
            self.assertGreaterEqual(result["summary"]["sheets"], 3)
            self.assertGreaterEqual(result["summary"]["image"], 4)
            self.assertEqual(result["summary"]["media_parts"], 4)
            images = [obj for sheet in result["sheets"] for obj in sheet["drawing_objects"] if obj["kind"] == "image"]
            self.assertTrue(all(obj["anchor"]["from"]["cell"] for obj in images))
            self.assertTrue(all(obj["media"]["sha256"] for obj in images))
            self.assertTrue(all(Path(obj["media"]["extracted_path"]).exists() for obj in images))
            self.assertTrue(all(obj["context"]["nearest_cells"] for obj in images))

    def test_merged_ranges(self):
        result = parse_workbook(FIXTURES / "openpyxl_merge_range.xlsx")
        self.assertGreaterEqual(result["summary"]["merged_ranges"], 1)
        self.assertTrue(any(sheet["merged_ranges"] for sheet in result["sheets"]))

    def test_charts_and_references(self):
        result = parse_workbook(FIXTURES / "openpyxl_charts.xlsx")
        self.assertGreaterEqual(result["summary"]["chart"], 1)
        charts = [obj["chart"] for sheet in result["sheets"] for obj in sheet["drawing_objects"] if obj["kind"] == "chart"]
        self.assertTrue(any(chart["data_references"] for chart in charts))

    def test_json_serializable(self):
        result = parse_workbook(FIXTURES / "markitdown_xlsx_complex_layout.xlsx")
        json.dumps(result, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()

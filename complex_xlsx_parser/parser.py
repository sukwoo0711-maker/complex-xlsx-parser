from __future__ import annotations

import hashlib
import posixpath
import re
import struct
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree as ET


NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
}
RID = f"{{{NS['r']}}}id"
EMBED = f"{{{NS['r']}}}embed"
CELL_REF = re.compile(r"^\$?([A-Z]+)\$?(\d+)$")
DEFAULT_MAX_INPUT_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_PART_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_MEDIA_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_TOTAL_UNCOMPRESSED = 2 * 1024 * 1024 * 1024
DEFAULT_MAX_ZIP_ENTRIES = 100_000
DEFAULT_MAX_COMPRESSION_RATIO = 1000.0
DEFAULT_MAX_CELLS = 2_000_000
DEFAULT_MAX_CONTEXT_RADIUS = 100


def _read_part(zf: ZipFile, part: str, max_bytes: int | None = None) -> bytes:
    limit = max_bytes if max_bytes is not None else getattr(zf, "_scene_max_part_bytes")
    try:
        info = zf.getinfo(part)
    except KeyError as exc:
        raise ValueError(f"Missing OOXML part: {part}") from exc
    if info.file_size > limit:
        raise ValueError(f"OOXML part exceeds byte limit ({limit}): {part}")
    data = zf.read(info)
    if len(data) != info.file_size:
        raise ValueError(f"OOXML part size mismatch: {part}")
    return data


def _xml(zf: ZipFile, part: str) -> ET.Element:
    try:
        data = _read_part(zf, part)
        if re.search(br"<!\s*(?:DOCTYPE|ENTITY)\b", data, re.IGNORECASE):
            raise ValueError(f"DTD/entity declarations are not allowed in OOXML XML: {part}")
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError(f"Malformed XML part: {part}: {exc}") from exc


def _rels_name(part: str) -> str:
    directory, name = posixpath.split(part)
    return posixpath.join(directory, "_rels", name + ".rels")


def _resolve(part: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def _relationships(zf: ZipFile, part: str) -> dict[str, dict[str, str]]:
    rels_part = _rels_name(part)
    if rels_part not in zf.namelist():
        return {}
    root = _xml(zf, rels_part)
    result = {}
    for rel in root.findall("rel:Relationship", NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target", "")
        if rel_id:
            result[rel_id] = {
                "target": target if rel.attrib.get("TargetMode") == "External" else _resolve(part, target),
                "type": rel.attrib.get("Type", ""),
                "external": rel.attrib.get("TargetMode") == "External",
            }
    return result


def _col_to_number(col: str) -> int:
    value = 0
    for char in col:
        value = value * 26 + ord(char) - 64
    return value


def _number_to_col(value: int) -> str:
    result = ""
    while value:
        value, rem = divmod(value - 1, 26)
        result = chr(65 + rem) + result
    return result or "A"


def _split_ref(ref: str) -> tuple[int, int]:
    match = CELL_REF.match(ref.upper())
    if not match:
        raise ValueError(f"Invalid cell reference: {ref}")
    return int(match.group(2)), _col_to_number(match.group(1))


def _marker(node: ET.Element | None) -> dict[str, Any] | None:
    if node is None:
        return None
    values = {}
    for key in ("col", "colOff", "row", "rowOff"):
        child = node.find(f"xdr:{key}", NS)
        values[key] = int(child.text or 0) if child is not None else 0
    values["cell"] = f"{_number_to_col(values['col'] + 1)}{values['row'] + 1}"
    return values


def _image_info(data: bytes, part: str) -> dict[str, Any]:
    width = height = None
    media_type = Path(part).suffix.lower().lstrip(".") or "unknown"
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        media_type = "png"
    elif data[:2] == b"\xff\xd8":
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            if marker in range(0xC0, 0xC4):
                height, width = struct.unpack(">HH", data[index + 5:index + 9])
                media_type = "jpeg"
                break
            if index + 4 > len(data):
                break
            length = struct.unpack(">H", data[index + 2:index + 4])[0]
            index += max(2, length + 2)
    return {
        "part": part,
        "media_type": media_type,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "width_px": width,
        "height_px": height,
    }


def _shared_strings(zf: ZipFile) -> list[str]:
    part = "xl/sharedStrings.xml"
    if part not in zf.namelist():
        return []
    root = _xml(zf, part)
    return ["".join(t.text or "" for t in si.findall(".//m:t", NS)) for si in root.findall("m:si", NS)]


def _styles(zf: ZipFile) -> dict[int, dict[str, Any]]:
    part = "xl/styles.xml"
    if part not in zf.namelist():
        return {}
    root = _xml(zf, part)
    custom = {int(n.attrib["numFmtId"]): n.attrib.get("formatCode", "") for n in root.findall("m:numFmts/m:numFmt", NS)}
    result = {}
    for index, xf in enumerate(root.findall("m:cellXfs/m:xf", NS)):
        num_fmt_id = int(xf.attrib.get("numFmtId", 0))
        result[index] = {"num_fmt_id": num_fmt_id, "format_code": custom.get(num_fmt_id)}
    return result


def _cell_value(cell: ET.Element, shared: list[str]) -> Any:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in cell.findall(".//m:t", NS))
    value_node = cell.find("m:v", NS)
    if value_node is None:
        return None
    raw = value_node.text or ""
    if cell_type == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return raw
    if cell_type in ("str", "e"):
        return raw
    if cell_type == "b":
        return raw == "1"
    if re.fullmatch(r"[+-]?\d+", raw):
        return int(raw)
    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except ValueError:
        return raw


def _parse_sheet_cells(root: ET.Element, shared: list[str], styles: dict[int, dict[str, Any]]) -> tuple[list[dict], dict[str, dict]]:
    cells = []
    by_ref = {}
    for cell in root.findall(".//m:sheetData/m:row/m:c", NS):
        ref = cell.attrib.get("r")
        if not ref:
            continue
        formula_node = cell.find("m:f", NS)
        value_node = cell.find("m:v", NS)
        style_id = int(cell.attrib.get("s", 0))
        value = _cell_value(cell, shared)
        item = {
            "ref": ref,
            "value": value,
            "raw_value": value_node.text if value_node is not None else None,
            "formula": formula_node.text if formula_node is not None else None,
            "formula_attributes": dict(formula_node.attrib) if formula_node is not None else None,
            "cached_value": value if formula_node is not None else None,
            "type": cell.attrib.get("t", "n"),
            "style_id": style_id,
            "number_format": styles.get(style_id),
        }
        cells.append(item)
        by_ref[ref] = item
    return cells, by_ref


def _range_bounds(ref: str) -> tuple[int, int, int, int]:
    left, _, right = ref.replace("$", "").partition(":")
    right = right or left
    r1, c1 = _split_ref(left)
    r2, c2 = _split_ref(right)
    return min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2)


def _context(by_ref: dict[str, dict], merges: list[str], start: dict | None, end: dict | None, radius: int) -> dict[str, Any]:
    if not start:
        return {"cells": [], "nearest_cells": [], "merged_ranges": []}
    r1, c1 = start["row"] + 1, start["col"] + 1
    r2 = (end or start)["row"] + 1
    c2 = (end or start)["col"] + 1
    r1, r2 = min(r1, r2), max(r1, r2)
    c1, c2 = min(c1, c2), max(c1, c2)
    cells = []
    for row in range(max(1, r1 - radius), r2 + radius + 1):
        for col in range(max(1, c1 - radius), c2 + radius + 1):
            ref = f"{_number_to_col(col)}{row}"
            item = by_ref.get(ref)
            if item and (item["value"] is not None or item["formula"]):
                cells.append({"ref": ref, "value": item["value"], "formula": item["formula"]})
    intersecting = []
    for merged in merges:
        mr1, mc1, mr2, mc2 = _range_bounds(merged)
        if not (mr2 < r1 or mr1 > r2 or mc2 < c1 or mc1 > c2):
            intersecting.append(merged)
    ranked = []
    for ref, item in by_ref.items():
        if item["value"] is None and not item["formula"]:
            continue
        row, col = _split_ref(ref)
        row_distance = max(r1 - row, 0, row - r2)
        col_distance = max(c1 - col, 0, col - c2)
        ranked.append((row_distance + col_distance, row, col, item))
    nearest = []
    for distance, _, _, item in sorted(ranked, key=lambda entry: entry[:3])[:12]:
        nearest.append({"ref": item["ref"], "value": item["value"], "formula": item["formula"], "distance": distance})
    return {"cells": cells, "nearest_cells": nearest, "merged_ranges": intersecting}


def _chart_summary(zf: ZipFile, part: str) -> dict[str, Any]:
    root = _xml(zf, part)
    title = " ".join(t.text or "" for t in root.findall(".//a:t", NS)).strip() or None
    refs = []
    for node in root.findall(".//c:f", NS):
        if node.text and node.text not in refs:
            refs.append(node.text)
    chart_types = []
    for node in root.iter():
        local = node.tag.rsplit("}", 1)[-1]
        if local.endswith("Chart") and local not in chart_types:
            chart_types.append(local)
    return {"part": part, "title": title, "types": chart_types, "data_references": refs}


def _parse_drawing(zf: ZipFile, part: str, by_ref: dict[str, dict], merges: list[str], radius: int) -> list[dict[str, Any]]:
    root = _xml(zf, part)
    rels = _relationships(zf, part)
    objects = []
    for index, anchor in enumerate(list(root)):
        anchor_type = anchor.tag.rsplit("}", 1)[-1]
        start = _marker(anchor.find("xdr:from", NS))
        end = _marker(anchor.find("xdr:to", NS))
        ext = anchor.find("xdr:ext", NS)
        anchor_info = {
            "type": anchor_type,
            "from": start,
            "to": end,
            "extent_emu": {"cx": int(ext.attrib.get("cx", 0)), "cy": int(ext.attrib.get("cy", 0))} if ext is not None else None,
        }
        common = {
            "id": f"{Path(part).stem}-object-{index + 1}",
            "anchor": anchor_info,
            "context": _context(by_ref, merges, start, end, radius),
        }
        pic = anchor.find("xdr:pic", NS)
        frame = anchor.find("xdr:graphicFrame", NS)
        shape = anchor.find("xdr:sp", NS)
        if pic is not None:
            props = pic.find("xdr:nvPicPr/xdr:cNvPr", NS)
            blip = pic.find("xdr:blipFill/a:blip", NS)
            rel = rels.get(blip.attrib.get(EMBED, ""), {}) if blip is not None else {}
            media_part = rel.get("target")
            item = {**common, "kind": "image", "name": props.attrib.get("name") if props is not None else None,
                    "description": props.attrib.get("descr") if props is not None else None,
                    "relationship_id": blip.attrib.get(EMBED) if blip is not None else None}
            if media_part and media_part in zf.namelist():
                item["media"] = _image_info(
                    _read_part(zf, media_part, getattr(zf, "_scene_max_media_bytes")), media_part
                )
            else:
                item["media"] = {"part": media_part, "missing": True}
            objects.append(item)
        elif frame is not None:
            props = frame.find("xdr:nvGraphicFramePr/xdr:cNvPr", NS)
            chart = frame.find(".//c:chart", NS)
            rel_id = chart.attrib.get(RID) if chart is not None else None
            target = rels.get(rel_id or "", {}).get("target")
            item = {**common, "kind": "chart", "name": props.attrib.get("name") if props is not None else None,
                    "relationship_id": rel_id, "chart": _chart_summary(zf, target) if target and target in zf.namelist() else {"part": target, "missing": True}}
            objects.append(item)
        elif shape is not None:
            props = shape.find("xdr:nvSpPr/xdr:cNvPr", NS)
            text = " ".join(t.text or "" for t in shape.findall(".//a:t", NS)).strip()
            objects.append({**common, "kind": "shape", "name": props.attrib.get("name") if props is not None else None, "text": text or None})
        else:
            objects.append({**common, "kind": "unsupported-drawing-object", "xml_tag": anchor_type})
    return objects


def parse_workbook(
    path: str | Path,
    *,
    extract_media: str | Path | None = None,
    context_radius: int = 2,
    redact_paths: bool = False,
    max_input_bytes: int = DEFAULT_MAX_INPUT_BYTES,
    max_part_bytes: int = DEFAULT_MAX_PART_BYTES,
    max_media_bytes: int = DEFAULT_MAX_MEDIA_BYTES,
    max_total_uncompressed: int = DEFAULT_MAX_TOTAL_UNCOMPRESSED,
    max_zip_entries: int = DEFAULT_MAX_ZIP_ENTRIES,
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO,
    max_cells: int = DEFAULT_MAX_CELLS,
    max_context_radius: int = DEFAULT_MAX_CONTEXT_RADIUS,
) -> dict[str, Any]:
    source = Path(path)
    if source.suffix.lower() not in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        raise ValueError("Expected an OOXML workbook (.xlsx, .xlsm, .xltx, or .xltm)")
    limits = (max_input_bytes, max_part_bytes, max_media_bytes, max_total_uncompressed,
              max_zip_entries, max_compression_ratio, max_cells, max_context_radius)
    if any(value <= 0 for value in limits):
        raise ValueError("All parser resource limits must be positive")
    if context_radius < 0 or context_radius > max_context_radius:
        raise ValueError(f"context_radius must be between 0 and {max_context_radius}")
    source_size = source.stat().st_size
    if source_size > max_input_bytes:
        raise ValueError(f"Workbook exceeds max_input_bytes ({max_input_bytes})")
    source_hash = hashlib.sha256()
    with source.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            source_hash.update(chunk)
    try:
        zf = ZipFile(source)
    except BadZipFile as exc:
        raise ValueError("Input is not a valid OOXML ZIP package") from exc

    with zf:
        infos = zf.infolist()
        if len(infos) > max_zip_entries:
            raise ValueError(f"OOXML package exceeds max_zip_entries ({max_zip_entries})")
        raw_names = [info.filename for info in infos]
        if len(raw_names) != len(set(raw_names)):
            raise ValueError("OOXML package contains duplicate ZIP entry names")
        total_uncompressed = sum(info.file_size for info in infos)
        if total_uncompressed > max_total_uncompressed:
            raise ValueError(
                f"OOXML package exceeds max_total_uncompressed ({max_total_uncompressed})"
            )
        for info in infos:
            member = PurePosixPath(info.filename)
            if (member.is_absolute() or ".." in member.parts or "\\" in info.filename
                    or "\x00" in info.filename):
                raise ValueError(f"Unsafe ZIP entry name: {info.filename!r}")
            if info.flag_bits & 0x1:
                raise ValueError(f"Encrypted ZIP entry is unsupported: {info.filename}")
            if info.file_size and (not info.compress_size or info.file_size / info.compress_size > max_compression_ratio):
                raise ValueError(
                    f"Suspicious compression ratio above {max_compression_ratio:g}: {info.filename}"
                )
        zf._scene_max_part_bytes = max_part_bytes
        zf._scene_max_media_bytes = max_media_bytes
        names = set(raw_names)
        if "xl/workbook.xml" not in names:
            raise ValueError("OOXML package does not contain xl/workbook.xml")
        shared = _shared_strings(zf)
        styles = _styles(zf)
        workbook = _xml(zf, "xl/workbook.xml")
        workbook_rels = _relationships(zf, "xl/workbook.xml")
        sheets = []
        all_media = {}
        warnings = []
        total_cells = 0

        for sheet_node in workbook.findall("m:sheets/m:sheet", NS):
            rel_id = sheet_node.attrib.get(RID)
            rel = workbook_rels.get(rel_id or "", {})
            sheet_part = rel.get("target")
            if not sheet_part or sheet_part not in names:
                warnings.append(f"Missing worksheet for {sheet_node.attrib.get('name')}")
                continue
            root = _xml(zf, sheet_part)
            cells, by_ref = _parse_sheet_cells(root, shared, styles)
            total_cells += len(cells)
            if total_cells > max_cells:
                raise ValueError(f"Workbook exceeds max_cells ({max_cells})")
            merges = [node.attrib.get("ref", "") for node in root.findall("m:mergeCells/m:mergeCell", NS) if node.attrib.get("ref")]
            sheet_rels = _relationships(zf, sheet_part)
            drawing_objects = []
            for drawing_node in root.findall("m:drawing", NS):
                drawing_rel = sheet_rels.get(drawing_node.attrib.get(RID, ""), {})
                drawing_part = drawing_rel.get("target")
                if drawing_part and drawing_part in names:
                    drawing_objects.extend(_parse_drawing(zf, drawing_part, by_ref, merges, context_radius))
                else:
                    warnings.append(f"Missing drawing part referenced by {sheet_part}")
            for item in drawing_objects:
                media = item.get("media")
                if media and media.get("part") and not media.get("missing"):
                    all_media[media["part"]] = media

            rows = [{"index": int(row.attrib.get("r", 0)), "height": float(row.attrib["ht"]) if "ht" in row.attrib else None,
                     "hidden": row.attrib.get("hidden") == "1"} for row in root.findall("m:sheetData/m:row", NS)]
            columns = [{"min": int(col.attrib.get("min", 0)), "max": int(col.attrib.get("max", 0)),
                        "width": float(col.attrib["width"]) if "width" in col.attrib else None,
                        "hidden": col.attrib.get("hidden") == "1"} for col in root.findall("m:cols/m:col", NS)]
            image_formulas = [c["ref"] for c in cells if c["formula"] and c["formula"].lstrip(" =").upper().startswith(("IMAGE(", "_XLFN.IMAGE("))]
            sheets.append({
                "name": sheet_node.attrib.get("name"),
                "state": sheet_node.attrib.get("state", "visible"),
                "part": sheet_part,
                "dimension": (root.find("m:dimension", NS).attrib.get("ref") if root.find("m:dimension", NS) is not None else None),
                "cells": cells,
                "merged_ranges": merges,
                "rows": rows,
                "columns": columns,
                "drawing_objects": drawing_objects,
                "image_formula_cells": image_formulas,
            })

        if extract_media:
            destination = Path(extract_media).resolve()
            destination.mkdir(parents=True, exist_ok=True)
            for part, media in all_media.items():
                filename = f"{media['sha256'][:12]}-{Path(part).name}"
                extracted = destination / filename
                try:
                    extracted.resolve().relative_to(destination)
                except ValueError as exc:
                    raise ValueError(f"Unsafe extracted media path: {extracted}") from exc
                with extracted.open("xb") as stream:
                    stream.write(_read_part(zf, part, max_media_bytes))
                media["extracted_path"] = extracted.name if redact_paths else str(extracted.resolve())

        object_counts = {"image": 0, "chart": 0, "shape": 0, "unsupported-drawing-object": 0}
        for sheet in sheets:
            for obj in sheet["drawing_objects"]:
                object_counts[obj["kind"]] = object_counts.get(obj["kind"], 0) + 1
        unsupported_parts = {
            "rich_data": sorted(n for n in names if n.startswith("xl/richData/")),
            "external_links": sorted(n for n in names if n.startswith("xl/externalLinks/") and n.endswith(".xml")),
            "vml_drawings": sorted(n for n in names if n.startswith("xl/drawings/") and n.endswith(".vml")),
            "comments": sorted(n for n in names if n.startswith("xl/comments") and n.endswith(".xml")),
            "macros": sorted(n for n in names if n.endswith("vbaProject.bin")),
            "custom_xml": sorted(n for n in names if n.startswith("customXml/")),
        }
        return {
            "schema_version": "1.1",
            "parser_version": "0.3.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": {
                "path": source.name if redact_paths else str(source.resolve()),
                "path_redacted": redact_paths,
                "bytes": source_size,
                "sha256": source_hash.hexdigest(),
            },
            "summary": {
                "sheets": len(sheets),
                "cells": sum(len(s["cells"]) for s in sheets),
                "merged_ranges": sum(len(s["merged_ranges"]) for s in sheets),
                "drawing_objects": sum(object_counts.values()),
                **object_counts,
                "media_parts": len(all_media),
                "image_formula_cells": sum(len(s["image_formula_cells"]) for s in sheets),
            },
            "sheets": sheets,
            "media": list(all_media.values()),
            "unsupported_or_separate_parts": unsupported_parts,
            "resource_limits": {
                "max_input_bytes": max_input_bytes,
                "max_part_bytes": max_part_bytes,
                "max_media_bytes": max_media_bytes,
                "max_total_uncompressed": max_total_uncompressed,
                "max_zip_entries": max_zip_entries,
                "max_compression_ratio": max_compression_ratio,
                "max_cells": max_cells,
                "max_context_radius": max_context_radius,
            },
            "warnings": warnings,
        }

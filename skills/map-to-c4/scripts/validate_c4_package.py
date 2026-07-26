#!/usr/bin/env python3
"""Reject C4 packages that contain metadata pages or disconnected card grids.

Rendered SVG elements and relationships must carry stable model annotations:

  data-c4-element-id="..."
  data-c4-relationship-id="..."
  data-source-id="..."
  data-destination-id="..."
  data-label="..."

The relationship element (or one of its descendants) must use marker-end for a
visible arrowhead. This validator intentionally accepts SVG only so connectors
and model identity can be checked rather than inferred from prose.
"""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

FORBIDDEN_INDEX_TEXT = {
    "four-level coverage matrix",
    "coverage matrix",
    "evidence ledger",
    "overlap report",
    "validation checklist",
    "reverse-engineering checklist",
    "corrected scope",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.svg_sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"] or "")
        if tag == "object" and (values.get("type") == "image/svg+xml" or str(values.get("data", "")).endswith(".svg")):
            if values.get("data"):
                self.svg_sources.append(values["data"] or "")
        if tag == "img" and str(values.get("src", "")).endswith(".svg"):
            self.svg_sources.append(values["src"] or "")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def descendants_have_arrow(node: ET.Element) -> bool:
    for descendant in node.iter():
        if "marker-end" in descendant.attrib:
            return True
        if local_name(descendant.tag) in {"polygon", "polyline"} and "arrow" in " ".join(descendant.attrib.values()).lower():
            return True
    return False


def descendants_have_text(node: ET.Element) -> bool:
    return any(local_name(descendant.tag) == "text" and "".join(descendant.itertext()).strip() for descendant in node.iter())


def rectangle(node: ET.Element) -> tuple[float, float, float, float]:
    x, y = float(node.attrib["x"]), float(node.attrib["y"])
    return x, y, x + float(node.attrib["width"]), y + float(node.attrib["height"])


def rectangles_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float], gap: float = 0) -> bool:
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def point_inside(point: tuple[float, float], rect: tuple[float, float, float, float]) -> bool:
    return rect[0] < point[0] < rect[2] and rect[1] < point[1] < rect[3]


def rectangle_contains(outer: tuple[float, float, float, float], inner: tuple[float, float, float, float], gap: float = 0) -> bool:
    return outer[0] + gap < inner[0] and outer[1] + gap < inner[1] and inner[2] < outer[2] - gap and inner[3] < outer[3] - gap


def point_on_rectangle_edge(point: tuple[float, float], rect: tuple[float, float, float, float], tolerance: float = 1.1) -> bool:
    x, y = point
    horizontal = rect[0] - tolerance <= x <= rect[2] + tolerance and (abs(y - rect[1]) <= tolerance or abs(y - rect[3]) <= tolerance)
    vertical = rect[1] - tolerance <= y <= rect[3] + tolerance and (abs(x - rect[0]) <= tolerance or abs(x - rect[2]) <= tolerance)
    return horizontal or vertical


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    return orientation(a, b, c) * orientation(a, b, d) <= 0 and orientation(c, d, a) * orientation(c, d, b) <= 0 and not (
        max(a[0], b[0]) < min(c[0], d[0]) or max(c[0], d[0]) < min(a[0], b[0]) or
        max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1])
    )


def segment_hits_rectangle(a: tuple[float, float], b: tuple[float, float], rect: tuple[float, float, float, float]) -> bool:
    if point_inside(a, rect) or point_inside(b, rect):
        return True
    left, top, right, bottom = rect
    corners = ((left, top), (right, top), (right, bottom), (left, bottom))
    return any(segments_intersect(a, b, corners[index], corners[(index + 1) % 4]) for index in range(4))


def polyline_points(node: ET.Element) -> list[tuple[float, float]]:
    return [tuple(map(float, pair.split(","))) for pair in node.attrib.get("points", "").split()]


def collinear_overlap(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    if a[1] == b[1] == c[1] == d[1]:
        return min(max(a[0], b[0]), max(c[0], d[0])) - max(min(a[0], b[0]), min(c[0], d[0])) > 1
    if a[0] == b[0] == c[0] == d[0]:
        return min(max(a[1], b[1]), max(c[1], d[1])) - max(min(a[1], b[1]), min(c[1], d[1])) > 1
    return False


def svg_documents(page: Path, text: str, parser: PageParser) -> tuple[list[ET.Element], list[str]]:
    roots: list[ET.Element] = []
    failures: list[str] = []
    inline = re.findall(r"<svg\b.*?</svg>", text, flags=re.IGNORECASE | re.DOTALL)
    for index, source in enumerate(inline, start=1):
        try:
            roots.append(ET.fromstring(source))
        except ET.ParseError as exc:
            failures.append(f"{page}: inline SVG {index} is not valid XML: {exc}")
    for source in parser.svg_sources:
        svg_path = (page.parent / source.split("#", 1)[0]).resolve()
        if not svg_path.is_file():
            failures.append(f"{page}: linked SVG does not exist: {source}")
            continue
        try:
            roots.append(ET.parse(svg_path).getroot())
        except ET.ParseError as exc:
            failures.append(f"{page}: linked SVG is not valid XML ({source}): {exc}")
    return roots, failures


def validate_diagram_page(page: Path) -> list[str]:
    text = page.read_text(encoding="utf-8")
    lowered = text.lower()
    parser = PageParser()
    parser.feed(text)
    failures: list[str] = []
    roots, svg_failures = svg_documents(page, text, parser)
    failures.extend(svg_failures)

    if not roots:
        return failures + [f"{page}: no rendered SVG diagram; HTML cards and relationship prose do not count"]
    svg_has_title = any(
        any(local_name(node.tag) == "title" and "".join(node.itertext()).strip() for node in root.iter())
        for root in roots
    )
    if "<h1" not in lowered and not svg_has_title:
        failures.append(f"{page}: missing diagram title")
    if "legend" not in lowered and not any(root.attrib.get("data-c4-key") for root in roots):
        failures.append(f"{page}: missing diagram key/legend")

    element_ids: set[str] = set()
    element_nodes: dict[str, ET.Element] = {}
    relationships: list[ET.Element] = []
    relationship_ids: set[str] = set()
    for root in roots:
        for node in root.iter():
            element_id = node.attrib.get("data-c4-element-id")
            if element_id:
                if element_id in element_ids:
                    failures.append(f"{page}: duplicate rendered element ID: {element_id}")
                element_ids.add(element_id)
                element_nodes[element_id] = node
                if not any(node.attrib.get(name) for name in ("data-model-element-id", "data-model-boundary-id", "data-evidence-refs")):
                    failures.append(f"{page}: element {element_id} has no canonical or evidence provenance")
            relationship_id = node.attrib.get("data-c4-relationship-id")
            if relationship_id:
                if relationship_id in relationship_ids:
                    failures.append(f"{page}: duplicate rendered relationship ID: {relationship_id}")
                relationship_ids.add(relationship_id)
                relationships.append(node)
                if not any(node.attrib.get(name) for name in ("data-model-relationship-ids", "data-evidence-refs")):
                    failures.append(f"{page}: relationship {relationship_id} has no canonical or evidence provenance")

    if not element_ids:
        failures.append(f"{page}: SVG has no data-c4-element-id annotations")
    if not relationships:
        failures.append(f"{page}: SVG has no rendered relationship connectors")

    element_rectangles: dict[str, tuple[float, float, float, float]] = {}
    boundary_rectangles: dict[str, tuple[float, float, float, float]] = {}
    label_rectangles: dict[str, tuple[float, float, float, float]] = {}
    relationship_polylines: dict[str, list[tuple[float, float]]] = {}
    for root in roots:
        for node in root.iter():
            element_id = node.attrib.get("data-c4-element-id")
            if element_id:
                visual = next((child for child in node.iter() if local_name(child.tag) == "rect" and "element" in child.attrib.get("class", "").split()), None)
                if visual is not None:
                    element_rectangles[element_id] = rectangle(visual)
                boundary_visual = next((child for child in node.iter() if local_name(child.tag) == "rect" and "boundary" in child.attrib.get("class", "").split()), None)
                if boundary_visual is not None:
                    boundary_rectangles[element_id] = rectangle(boundary_visual)
            label_for = node.attrib.get("data-c4-relationship-label-for")
            if label_for and local_name(node.tag) == "rect":
                label_rectangles[label_for] = rectangle(node)

    for relationship in relationships:
        relationship_id = relationship.attrib.get("data-c4-relationship-id", "<unknown>")
        source = relationship.attrib.get("data-source-id")
        destination = relationship.attrib.get("data-destination-id")
        label = relationship.attrib.get("data-label", "").strip()
        if not source or source not in element_ids:
            failures.append(f"{page}: relationship {relationship_id} has missing/unknown source {source!r}")
        if not destination or destination not in element_ids:
            failures.append(f"{page}: relationship {relationship_id} has missing/unknown destination {destination!r}")
        if not label and not descendants_have_text(relationship):
            failures.append(f"{page}: relationship {relationship_id} has no visible label")
        if not descendants_have_arrow(relationship):
            failures.append(f"{page}: relationship {relationship_id} has no visible arrowhead")
        connector = next((child for child in relationship.iter() if local_name(child.tag) == "polyline" and child.attrib.get("class") == "relationship"), None)
        if connector is not None:
            points = polyline_points(connector)
            relationship_polylines[relationship_id] = points
            if len(points) < 2:
                failures.append(f"{page}: relationship {relationship_id} connector has fewer than two points")
            else:
                if source in element_rectangles and not point_on_rectangle_edge(points[0], element_rectangles[source]):
                    failures.append(f"{page}: connector {relationship_id} does not start on source {source}")
                if destination in element_rectangles and not point_on_rectangle_edge(points[-1], element_rectangles[destination]):
                    failures.append(f"{page}: connector {relationship_id} does not end on destination {destination}")
        if relationship_id not in label_rectangles:
            failures.append(f"{page}: relationship {relationship_id} has no measurable label background")

    if boundary_rectangles:
        for element_id, node in element_nodes.items():
            if node.attrib.get("data-inside-scope") == "true" and element_id in element_rectangles:
                if not any(rectangle_contains(boundary, element_rectangles[element_id], 3) for boundary in boundary_rectangles.values()):
                    failures.append(f"{page}: in-scope element {element_id} lies outside its rendered boundary")

    element_items = list(element_rectangles.items())
    label_items = list(label_rectangles.items())
    for index, (first_id, first) in enumerate(element_items):
        for second_id, second in element_items[index + 1:]:
            if rectangles_overlap(first, second, 3):
                failures.append(f"{page}: element overlap: {first_id} and {second_id}")
    for index, (first_id, first) in enumerate(label_items):
        for second_id, second in label_items[index + 1:]:
            if rectangles_overlap(first, second, 3):
                failures.append(f"{page}: relationship-label overlap: {first_id} and {second_id}")
        for element_id, element_rect in element_items:
            if rectangles_overlap(first, element_rect, 3):
                failures.append(f"{page}: relationship label {first_id} overlaps element {element_id}")

    all_segments: list[tuple[str, str | None, str | None, tuple[float, float], tuple[float, float]]] = []
    for relationship in relationships:
        relationship_id = relationship.attrib.get("data-c4-relationship-id", "<unknown>")
        source, destination = relationship.attrib.get("data-source-id"), relationship.attrib.get("data-destination-id")
        points = relationship_polylines.get(relationship_id, [])
        for a, b in zip(points, points[1:]):
            for element_id, element_rect in element_items:
                if element_id not in {source, destination} and segment_hits_rectangle(a, b, element_rect):
                    failures.append(f"{page}: connector {relationship_id} crosses element {element_id}")
            for label_id, label_rect in label_items:
                if label_id != relationship_id and segment_hits_rectangle(a, b, label_rect):
                    failures.append(f"{page}: connector {relationship_id} crosses label {label_id}")
            all_segments.append((relationship_id, source, destination, a, b))
    for index, (first_id, first_source, first_destination, a, b) in enumerate(all_segments):
        for second_id, second_source, second_destination, c, d in all_segments[index + 1:]:
            if first_id != second_id and collinear_overlap(a, b, c, d):
                failures.append(f"{page}: connector segments overlap: {first_id} and {second_id}")

    return failures


def validate_local_links(page: Path, hrefs: list[str]) -> list[str]:
    failures: list[str] = []
    for href in hrefs:
        parsed = urlsplit(href)
        if parsed.scheme or parsed.netloc or href.startswith(("#", "mailto:")):
            continue
        target_text = unquote(parsed.path)
        if not target_text:
            continue
        target = (page.parent / target_text).resolve()
        if not target.exists():
            failures.append(f"{page}: broken local link: {href}")
    return failures


def validate_index(root: Path) -> list[str]:
    index = root / "index.html"
    if not index.is_file():
        return [f"{index}: architecture index is missing"]
    text = index.read_text(encoding="utf-8")
    lowered = re.sub(r"\s+", " ", text.lower())
    failures = [f"{index}: public index contains skill/process metadata: {phrase}" for phrase in FORBIDDEN_INDEX_TEXT if phrase in lowered]
    if "<h1" not in lowered:
        failures.append(f"{index}: architecture index requires a subject-specific h1 heading")
    parser = PageParser()
    parser.feed(text)
    if not any(href.endswith("context.html") for href in parser.hrefs):
        failures.append(f"{index}: no link to a System Context diagram")
    if not any(href.endswith("containers.html") for href in parser.hrefs):
        failures.append(f"{index}: no link to a Container diagram")
    failures.extend(validate_local_links(index, parser.hrefs))
    return failures


def main() -> int:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("architecture_root", type=Path)
    args = argument_parser.parse_args()
    root = args.architecture_root.resolve()
    failures = validate_index(root)
    pages: list[Path] = []
    for page in sorted(root.rglob("*.html")):
        if page == root / "index.html":
            continue
        text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(text)
        if parser.svg_sources or re.search(r"<svg\b", text, flags=re.IGNORECASE):
            pages.append(page)
            failures.extend(validate_diagram_page(page))
            failures.extend(validate_local_links(page, parser.hrefs))
    if not pages:
        failures.append(f"{root}: no C4 diagram pages found")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"\nC4 package rejected: {len(failures)} failure(s) across {len(pages)} diagram page(s).")
        return 1
    print(f"C4 package accepted: {len(pages)} connected SVG diagram page(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

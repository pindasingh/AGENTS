#!/usr/bin/env python3
"""Render a connected C4 view JSON file to SVG and optional standalone HTML.

Uses only the Python standard library. See assets/preflight-view.json for the
input shape. This is a deliberately small renderer for environments where
Structurizr, PlantUML, Mermaid CLI, and Graphviz are unavailable.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import heapq
from html import escape
import itertools
import json
import math
from pathlib import Path
import textwrap

CONTEXT_LAYOUT_WIDTH = 1600
SCOPED_LAYOUT_WIDTH = 2000
MIN_CANVAS_WIDTH = 1050
BOX_W = 250
BOX_H = 135
GAP_X = 55
GAP_Y = 45


@dataclass
class Box:
    id: str
    name: str
    type: str
    description: str
    technology: str
    x: float
    y: float
    w: float = BOX_W
    h: float = BOX_H
    style: str = "external"
    model_element_id: str = ""
    model_boundary_id: str = ""
    evidence_refs: tuple[str, ...] = ()
    inside_scope: bool | None = None

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class RoutedRelationship:
    relationship: dict
    points: list[tuple[float, float]]
    label_x: float = 0
    label_y: float = 0
    label_w: float = 0
    label_h: float = 0
    label_lines: list[str] | None = None


def lines(value: str, width: int, maximum: int) -> list[str]:
    wrapped = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)
    if len(wrapped) > maximum:
        wrapped = wrapped[:maximum]
        wrapped[-1] = wrapped[-1].rstrip(".,;: ") + "…"
    return wrapped or [""]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def c4_type(value: str) -> str:
    """Return the canonical C4 type represented by a display type."""
    lowered = value.strip().lower()
    require("group" not in lowered, f"pseudo-group element type is not allowed: {value}")
    for candidate in ("software system", "person", "container", "component"):
        if lowered == candidate or lowered.startswith(candidate + ":"):
            return candidate
    code_tokens = ("class", "interface", "function", "table", "enum", "object", "dataclass", "entity", "event", "contract", "exception", "module")
    if any(token in lowered for token in code_tokens):
        return "code"
    return "unknown"


def validate(view: dict) -> None:
    diagram_type = view.get("diagramType")
    require(diagram_type in {"System Context", "Container", "Component", "Code", "Dynamic"}, "diagramType must be System Context, Container, Component, Code, or Dynamic")
    require(isinstance(view.get("title"), str) and view["title"].strip(), "title is required")
    scope = view.get("scope")
    require(isinstance(scope, dict), "scope object is required")
    for field in ("id", "name", "type", "description"):
        require(isinstance(scope.get(field), str) and scope[field].strip(), f"scope.{field} is required")
    elements = view.get("elements")
    relationships = view.get("relationships")
    require(isinstance(elements, list), "elements must be a list")
    require(isinstance(relationships, list) and relationships, "relationships must be a non-empty list")

    all_elements = [scope, *elements]
    ids: set[str] = set()
    element_types: dict[str, str] = {}
    for element in all_elements:
        for field in ("id", "name", "type", "description"):
            require(isinstance(element.get(field), str) and element[field].strip(), f"element {element.get('id', '<unknown>')}.{field} is required")
        require(element["id"] not in ids, f"duplicate element id: {element['id']}")
        ids.add(element["id"])
        canonical_type = c4_type(element["type"])
        require(canonical_type != "unknown", f"unknown C4 element type for {element['id']}: {element['type']}")
        element_types[element["id"]] = canonical_type
        if canonical_type in {"container", "component"}:
            require(isinstance(element.get("technology"), str) and element["technology"].strip(), f"technology is required for {element['id']}")
        if diagram_type != "System Context" and element is not scope:
            require(isinstance(element.get("insideScope"), bool), f"insideScope boolean is required for {element['id']}")

    expected_scope = {"System Context": "software system", "Container": "software system", "Component": "container", "Code": "component"}
    if diagram_type in expected_scope:
        require(element_types[scope["id"]] == expected_scope[diagram_type], f"{diagram_type} scope must be a {expected_scope[diagram_type]}")

    if diagram_type == "System Context":
        require(all(element_types[element["id"]] in {"person", "software system"} for element in elements), "System Context elements must be People or Software Systems")
        require(all(not str(element.get("technology", "")).strip() for element in all_elements), "System Context must omit technology and implementation detail")
    elif diagram_type == "Container":
        require(all(element_types[element["id"]] == "container" for element in elements if element["insideScope"]), "Container in-scope elements must be Containers")
        require(all(element_types[element["id"]] in {"person", "software system"} for element in elements if not element["insideScope"]), "Container supporting elements must be People or Software Systems")
    elif diagram_type == "Component":
        require(all(element_types[element["id"]] == "component" for element in elements if element["insideScope"]), "Component in-scope elements must be Components")
        require(all(element_types[element["id"]] in {"person", "software system", "container"} for element in elements if not element["insideScope"]), "Component supporting elements must be People, Software Systems, or Containers")
    elif diagram_type == "Code":
        require(all(element["insideScope"] and element_types[element["id"]] == "code" for element in elements), "Code elements must be code-level children inside the scoped Component")

    relationship_ids: set[str] = set()
    interaction_orders: set[int] = set()
    for relationship in relationships:
        for field in ("id", "source", "destination", "description"):
            require(isinstance(relationship.get(field), str) and relationship[field].strip(), f"relationship {relationship.get('id', '<unknown>')}.{field} is required")
        require(relationship["id"] not in relationship_ids, f"duplicate relationship id: {relationship['id']}")
        relationship_ids.add(relationship["id"])
        require(relationship["source"] in ids, f"unknown relationship source: {relationship['source']}")
        require(relationship["destination"] in ids, f"unknown relationship destination: {relationship['destination']}")
        require(relationship["source"] != relationship["destination"], f"self relationship is not allowed: {relationship['id']}")
        if diagram_type == "Container":
            require(isinstance(relationship.get("technology"), str) and relationship["technology"].strip(), f"technology/protocol is required for Container relationship {relationship['id']}")
        if diagram_type == "System Context":
            require(not str(relationship.get("technology", "")).strip(), f"System Context relationship must omit technology: {relationship['id']}")
        if diagram_type == "Dynamic":
            order = relationship.get("order")
            require(isinstance(order, int) and not isinstance(order, bool) and order > 0, f"positive integer order is required for Dynamic relationship {relationship['id']}")
            require(order not in interaction_orders, f"duplicate Dynamic interaction order: {order}")
            interaction_orders.add(order)

    if diagram_type == "System Context":
        require(all(scope["id"] in {relationship["source"], relationship["destination"]} for relationship in relationships), "System Context relationships must connect directly to the scoped Software System")
        require(all(any(scope["id"] in {relationship["source"], relationship["destination"]} and element["id"] in {relationship["source"], relationship["destination"]} for relationship in relationships) for element in elements), "System Context supporting elements must connect directly to the scoped Software System")
    if diagram_type in {"Container", "Component"}:
        internal_ids = {element["id"] for element in elements if element["insideScope"]}
        require(all(bool(internal_ids & {relationship["source"], relationship["destination"]}) for relationship in relationships), f"{diagram_type} relationships must connect to an in-scope element")
        for element in (item for item in elements if not item["insideScope"]):
            require(any(element["id"] in {relationship["source"], relationship["destination"]} and bool(internal_ids & {relationship["source"], relationship["destination"]}) for relationship in relationships), f"supporting element {element['id']} must connect directly to an in-scope element")


def style_for(element: dict, scope_id: str) -> str:
    if element["id"] == scope_id:
        return "system"
    value = element["type"].lower()
    if value.startswith("person"):
        return "person"
    if value.startswith("container"):
        return "container"
    if value.startswith("component"):
        return "component"
    if any(token in value for token in ("class", "interface", "function", "code", "table", "enum", "object", "dataclass", "entity", "event", "contract", "exception")):
        return "code"
    return "external"


def distribute(items: list[dict], x: float, height: float) -> list[Box]:
    if not items:
        return []
    available = max(height - 170, len(items) * (BOX_H + 20))
    step = available / max(1, len(items))
    start = 100 + max(0, (available - len(items) * BOX_H) / (len(items) + 1))
    boxes = []
    for index, item in enumerate(items):
        y = start + index * step
        boxes.append(make_box(item, x, y, "external"))
    return boxes


def optional_string(item: dict, field: str) -> str:
    value = item.get(field)
    return value.strip() if isinstance(value, str) else ""


def reference_tuple(item: dict, field: str) -> tuple[str, ...]:
    value = item.get(field)
    if not isinstance(value, list):
        return ()
    return tuple(entry.strip() for entry in value if isinstance(entry, str) and entry.strip())


def make_box(element: dict, x: float, y: float, default_style: str, scope_id: str = "") -> Box:
    position = element.get("position") or {}
    return Box(
        id=element["id"], name=element["name"], type=element["type"],
        description=element["description"], technology=element.get("technology", ""),
        x=float(position.get("x", x)), y=float(position.get("y", y)),
        w=float(position.get("width", BOX_W)), h=float(position.get("height", BOX_H)),
        style=style_for(element, scope_id) if scope_id else default_style,
        model_element_id=optional_string(element, "modelElementId"),
        model_boundary_id=optional_string(element, "modelBoundaryId"),
        evidence_refs=reference_tuple(element, "evidenceRefs"),
        inside_scope=element.get("insideScope") if isinstance(element.get("insideScope"), bool) else None,
    )


def layout_context(view: dict) -> tuple[list[Box], tuple[float, float, float, float] | None, int]:
    scope = view["scope"]
    elements = view["elements"]
    incoming_ids = {r["source"] for r in view["relationships"] if r["destination"] == scope["id"]}
    outgoing_ids = {r["destination"] for r in view["relationships"] if r["source"] == scope["id"]}
    left = [e for e in elements if e["id"] in incoming_ids or e["type"].lower().startswith("person")]
    right = [e for e in elements if e not in left]
    height = max(720, 220 + max(len(left), len(right)) * 170)
    scope_box = make_box(scope, (CONTEXT_LAYOUT_WIDTH - BOX_W) / 2, (height - BOX_H) / 2, "system", scope["id"])
    boxes = [scope_box]
    boxes.extend(distribute(left, 70, height))
    boxes.extend(distribute(right, CONTEXT_LAYOUT_WIDTH - BOX_W - 70, height))
    for box, element in zip(boxes[1:], [*left, *right]):
        box.style = style_for(element, scope["id"])
    return boxes, None, height


def layout_scoped(view: dict) -> tuple[list[Box], tuple[float, float, float, float], int]:
    scope = view["scope"]
    internal = [e for e in view["elements"] if e.get("insideScope")]
    external = [e for e in view["elements"] if not e.get("insideScope")]
    columns = min(4, max(1, len(internal)))
    rows = math.ceil(len(internal) / columns) if internal else 1
    boundary_y = 105
    boundary_w = max(940, columns * BOX_W + (columns + 1) * GAP_X)
    boundary_x = (SCOPED_LAYOUT_WIDTH - boundary_w) / 2
    boundary_h = max(310, 100 + rows * (BOX_H + GAP_Y))
    height = max(720, int(boundary_y + boundary_h + 180), 220 + math.ceil(len(external) / 2) * 165)
    boxes: list[Box] = []
    for index, element in enumerate(internal):
        row, column = divmod(index, columns)
        total_w = columns * BOX_W + (columns - 1) * GAP_X
        x = boundary_x + (boundary_w - total_w) / 2 + column * (BOX_W + GAP_X)
        y = boundary_y + 70 + row * (BOX_H + GAP_Y)
        boxes.append(make_box(element, x, y, "container", scope["id"]))

    incoming_targets = {r["source"] for r in view["relationships"] if any(e["id"] == r["destination"] and e.get("insideScope") for e in view["elements"])}
    left = [e for e in external if e["id"] in incoming_targets or e["type"].lower().startswith("person")]
    right = [e for e in external if e not in left]
    boxes.extend(distribute(left, 35, height))
    boxes.extend(distribute(right, SCOPED_LAYOUT_WIDTH - BOX_W - 35, height))
    for box, element in zip(boxes[len(internal):], [*left, *right]):
        box.style = style_for(element, scope["id"])
    return boxes, (boundary_x, boundary_y, boundary_w, boundary_h), height


GRID = 20
ROUTE_MARGIN = 22


def box_rect(box: Box, margin: float = 0) -> tuple[float, float, float, float]:
    return box.x - margin, box.y - margin, box.x + box.w + margin, box.y + box.h + margin


def rects_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float], gap: float = 0) -> bool:
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


def simplify_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for point in points:
        if result and point == result[-1]:
            continue
        if len(result) >= 2:
            a, b = result[-2], result[-1]
            if (a[0] == b[0] == point[0]) or (a[1] == b[1] == point[1]):
                result[-1] = point
                continue
        result.append(point)
    return result


def ports(box: Box) -> list[tuple[str, int, tuple[float, float], tuple[float, float], tuple[int, int]]]:
    result = []
    for side in ("left", "right", "top", "bottom"):
        for slot in (-30, 30):
            if side == "left":
                edge = (box.x, box.cy + slot); outside = (box.x - ROUTE_MARGIN, box.cy + slot)
            elif side == "right":
                edge = (box.x + box.w, box.cy + slot); outside = (box.x + box.w + ROUTE_MARGIN, box.cy + slot)
            elif side == "top":
                edge = (box.cx + slot, box.y); outside = (box.cx + slot, box.y - ROUTE_MARGIN)
            else:
                edge = (box.cx + slot, box.y + box.h); outside = (box.cx + slot, box.y + box.h + ROUTE_MARGIN)
            grid = (round(outside[0] / GRID), round(outside[1] / GRID))
            result.append((side, slot, edge, outside, grid))
    return result


def astar_route(start: tuple[int, int], end: tuple[int, int], boxes: list[Box], occupied_edges: set[tuple[tuple[int, int], tuple[int, int]]], canvas_width: int, route_bottom: int) -> tuple[float, list[tuple[int, int]]] | None:
    min_y = 4
    max_x = max(1, canvas_width // GRID)
    max_y = max(min_y + 1, route_bottom // GRID)

    def blocked(node: tuple[int, int]) -> bool:
        if node in {start, end}:
            return False
        x, y = node[0] * GRID, node[1] * GRID
        if node[0] < 1 or node[0] > max_x - 1 or node[1] < min_y or node[1] > max_y:
            return True
        return any(left <= x <= right and top <= y <= bottom for left, top, right, bottom in (box_rect(box, 12) for box in boxes))

    counter = itertools.count()
    queue: list[tuple[float, float, int, tuple[int, int], tuple[int, int] | None]] = []
    heapq.heappush(queue, (0, 0, next(counter), start, None))
    best: dict[tuple[tuple[int, int], tuple[int, int] | None], float] = {(start, None): 0}
    previous: dict[tuple[tuple[int, int], tuple[int, int] | None], tuple[tuple[int, int], tuple[int, int] | None] | None] = {(start, None): None}
    final_state = None
    while queue:
        _, cost, _, node, direction = heapq.heappop(queue)
        state = (node, direction)
        if cost != best.get(state):
            continue
        if node == end:
            final_state = state
            break
        for new_direction in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (node[0] + new_direction[0], node[1] + new_direction[1])
            if blocked(neighbour):
                continue
            edge = tuple(sorted((node, neighbour)))
            if edge in occupied_edges:
                continue
            bend = 0.7 if direction is not None and direction != new_direction else 0
            new_cost = cost + 1 + bend
            new_state = (neighbour, new_direction)
            if new_cost >= best.get(new_state, float("inf")):
                continue
            best[new_state] = new_cost
            previous[new_state] = state
            heuristic = abs(neighbour[0] - end[0]) + abs(neighbour[1] - end[1])
            heapq.heappush(queue, (new_cost + heuristic, new_cost, next(counter), neighbour, new_direction))
    if final_state is None:
        return None
    path = []
    state = final_state
    while state is not None:
        path.append(state[0])
        state = previous[state]
    path.reverse()
    return best[final_state], path


def route_relationships(relationships: list[dict], boxes_by_id: dict[str, Box], canvas_width: int, route_bottom: int) -> list[RoutedRelationship]:
    boxes = list(boxes_by_id.values())
    occupied_edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    used_ports: dict[tuple[str, str, int], int] = {}
    routed: dict[str, RoutedRelationship] = {}
    ordered = sorted(relationships, key=lambda rel: math.hypot(boxes_by_id[rel["destination"]].cx - boxes_by_id[rel["source"]].cx, boxes_by_id[rel["destination"]].cy - boxes_by_id[rel["source"]].cy), reverse=True)
    for relationship in ordered:
        source = boxes_by_id[relationship["source"]]
        destination = boxes_by_id[relationship["destination"]]
        candidates = []
        for source_port in ports(source):
            for destination_port in ports(destination):
                result = astar_route(source_port[4], destination_port[4], boxes, occupied_edges, canvas_width, route_bottom)
                if result is None:
                    continue
                cost, grid_path = result
                port_cost = 25 * used_ports.get((source.id, source_port[0], source_port[1]), 0) + 25 * used_ports.get((destination.id, destination_port[0], destination_port[1]), 0)
                candidates.append((cost + port_cost, source_port, destination_port, grid_path))
        require(bool(candidates), f"no collision-free connector route for relationship {relationship['id']}")
        _, source_port, destination_port, grid_path = min(candidates, key=lambda candidate: candidate[0])
        grid_points = [(x * GRID, y * GRID) for x, y in grid_path]
        points = simplify_points([source_port[2], source_port[3], *grid_points, destination_port[3], destination_port[2]])
        routed[relationship["id"]] = RoutedRelationship(relationship, points)
        occupied_edges.update(tuple(sorted((a, b))) for a, b in zip(grid_path[1:-2], grid_path[2:-1]))
        used_ports[(source.id, source_port[0], source_port[1])] = used_ports.get((source.id, source_port[0], source_port[1]), 0) + 1
        used_ports[(destination.id, destination_port[0], destination_port[1])] = used_ports.get((destination.id, destination_port[0], destination_port[1]), 0) + 1
    return [routed[relationship["id"]] for relationship in relationships]


def segment_bbox(a: tuple[float, float], b: tuple[float, float], margin: float = 0) -> tuple[float, float, float, float]:
    return min(a[0], b[0]) - margin, min(a[1], b[1]) - margin, max(a[0], b[0]) + margin, max(a[1], b[1]) + margin


def place_relationship_labels(routes: list[RoutedRelationship], boxes: list[Box], canvas_width: int, route_bottom: int, boundary: tuple[float, float, float, float] | None) -> None:
    labels: list[tuple[float, float, float, float]] = []
    element_obstacles = [box_rect(box, 7) for box in boxes]
    if boundary:
        element_obstacles.append((boundary[0], boundary[1], boundary[0] + min(420, boundary[2]), boundary[1] + 38))
    all_segments = [(route.relationship["id"], a, b) for route in routes for a, b in zip(route.points, route.points[1:])]
    for route in sorted(routes, key=lambda item: -max(math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in zip(item.points, item.points[1:]))):
        label = route.relationship["description"]
        if route.relationship.get("order") is not None:
            label = f"{route.relationship['order']}. {label}"
        if route.relationship.get("technology"):
            label += f" [{route.relationship['technology']}]"
        label_lines = lines(label, 38, 3)
        width = min(310, max(130, max(len(line) for line in label_lines) * 7.2 + 18))
        height = len(label_lines) * 17 + 10
        segments = sorted(zip(route.points, route.points[1:]), key=lambda pair: -math.hypot(pair[1][0]-pair[0][0], pair[1][1]-pair[0][1]))
        chosen = None
        for a, b in segments:
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy) or 1
            nx, ny = -dy / length, dx / length
            for fraction in (0.5, 0.3, 0.7, 0.15, 0.85):
                base_x, base_y = a[0] + dx * fraction, a[1] + dy * fraction
                for offset in (0, 24, -24, 46, -46, 70, -70, 96, -96, 124, -124, 160, -160, 220, -220, 280, -280):
                    cx, cy = base_x + nx * offset, base_y + ny * offset
                    rect = (cx - width/2, cy - height/2, cx + width/2, cy + height/2)
                    if rect[0] < 8 or rect[2] > canvas_width - 8 or rect[1] < 68 or rect[3] > route_bottom:
                        continue
                    if any(rects_overlap(rect, obstacle, 3) for obstacle in element_obstacles + labels):
                        continue
                    if any(other_id != route.relationship["id"] and rects_overlap(rect, segment_bbox(sa, sb, 3)) for other_id, sa, sb in all_segments):
                        continue
                    chosen = (cx, cy, rect)
                    break
                if chosen:
                    break
            if chosen:
                break
        if chosen is None:
            fallback = []
            for cy in range(90 + math.ceil(height / 2), math.floor(route_bottom - height / 2), 20):
                for cx in range(math.ceil(width / 2) + 10, math.floor(canvas_width - width / 2) - 10, 20):
                    rect = (cx - width/2, cy - height/2, cx + width/2, cy + height/2)
                    if any(rects_overlap(rect, obstacle, 3) for obstacle in element_obstacles + labels):
                        continue
                    if any(other_id != route.relationship["id"] and rects_overlap(rect, segment_bbox(sa, sb, 3)) for other_id, sa, sb in all_segments):
                        continue
                    distance = min(math.hypot(cx - px, cy - py) for px, py in route.points)
                    fallback.append((distance, cx, cy, rect))
            if fallback:
                _, cx, cy, rect = min(fallback, key=lambda candidate: candidate[0])
                chosen = (cx, cy, rect)
        require(chosen is not None, f"no collision-free label position for relationship {route.relationship['id']}")
        route.label_x, route.label_y, rect = chosen
        route.label_w, route.label_h, route.label_lines = width, height, label_lines
        labels.append(rect)


def svg_text(x: float, y: float, values: list[str], css_class: str, line_height: int = 17) -> str:
    tspans = "".join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else line_height}">{escape(value)}</tspan>' for i, value in enumerate(values))
    return f'<text class="{css_class}" x="{x:.1f}" y="{y:.1f}">{tspans}</text>'


def provenance_attributes(model_element_id: str = "", model_boundary_id: str = "", evidence_refs: tuple[str, ...] = ()) -> str:
    attributes = []
    if model_element_id:
        attributes.append(f'data-model-element-id="{escape(model_element_id)}"')
    if model_boundary_id:
        attributes.append(f'data-model-boundary-id="{escape(model_boundary_id)}"')
    if evidence_refs:
        attributes.append(f'data-evidence-refs="{escape(" | ".join(evidence_refs))}"')
    return (" " + " ".join(attributes)) if attributes else ""


def render_box(box: Box) -> str:
    name = lines(box.name, 27, 2)
    description = lines(box.description, 34, 3)
    type_line = f"[{box.type}]"
    tech = lines(box.technology, 35, 1) if box.technology else []
    name_y = box.y + 31
    type_y = name_y + len(name) * 20 + 4
    desc_y = type_y + 22
    tone = " dark-text" if box.style in {"component", "code"} else ""
    inside = "" if box.inside_scope is None else f' data-inside-scope="{str(box.inside_scope).lower()}"'
    provenance = provenance_attributes(box.model_element_id, box.model_boundary_id, box.evidence_refs)
    parts = [
        f'<g data-c4-element-id="{escape(box.id)}"{inside}{provenance}>',
        f'<rect class="element {box.style}" x="{box.x:.1f}" y="{box.y:.1f}" width="{box.w:.1f}" height="{box.h:.1f}" rx="5"/>',
        svg_text(box.cx, name_y, name, f"element-name{tone}", 20),
        svg_text(box.cx, type_y, [type_line], f"element-type{tone}"),
        svg_text(box.cx, desc_y, description, f"element-description{tone}"),
    ]
    if tech:
        parts.append(svg_text(box.cx, box.y + box.h - 14, [f"Technology: {tech[0]}"], f"element-tech{tone}"))
    parts.append("</g>")
    return "".join(parts)


def render_relationship(route: RoutedRelationship) -> str:
    relationship = route.relationship
    require(route.label_lines is not None, f"relationship label was not placed: {relationship['id']}")
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in route.points)
    rect_x = route.label_x - route.label_w / 2
    rect_y = route.label_y - route.label_h / 2
    text_y = route.label_y - (len(route.label_lines) - 1) * 8
    model_ids = reference_tuple(relationship, "modelRelationshipIds")
    evidence = reference_tuple(relationship, "evidenceRefs")
    provenance = ""
    if model_ids:
        provenance += f' data-model-relationship-ids="{escape(" | ".join(model_ids))}"'
    if evidence:
        provenance += f' data-evidence-refs="{escape(" | ".join(evidence))}"'
    return (
        f'<g data-c4-relationship-id="{escape(relationship["id"])}" data-source-id="{escape(relationship["source"])}" '
        f'data-destination-id="{escape(relationship["destination"])}" data-label="{escape(relationship["description"])}" '
        f'data-order="{escape(str(relationship.get("order", "")))}"{provenance}>'
        f'<polyline class="relationship-halo" points="{points}"/>'
        f'<polyline class="relationship" points="{points}" marker-end="url(#arrow)"/>'
        f'<rect data-c4-relationship-label-for="{escape(relationship["id"])}" class="relationship-label-bg" x="{rect_x:.1f}" y="{rect_y:.1f}" width="{route.label_w:.1f}" height="{route.label_h:.1f}" rx="3"/>'
        f'{svg_text(route.label_x, text_y, route.label_lines, "relationship-label", 17)}</g>'
    )


def fit_to_content(boxes: list[Box], boundary: tuple[float, float, float, float] | None) -> tuple[tuple[float, float, float, float] | None, int, int, int]:
    left = min([box.x for box in boxes] + ([boundary[0]] if boundary else []))
    right = max([box.x + box.w for box in boxes] + ([boundary[0] + boundary[2]] if boundary else []))
    top = min([box.y for box in boxes] + ([boundary[1]] if boundary else []))
    bottom = max([box.y + box.h for box in boxes] + ([boundary[1] + boundary[3]] if boundary else []))
    shift_x = 40 - left
    shift_y = 90 - top
    for box in boxes:
        box.x += shift_x
        box.y += shift_y
    shifted_boundary = None
    if boundary:
        shifted_boundary = (boundary[0] + shift_x, boundary[1] + shift_y, boundary[2], boundary[3])
    content_right = right + shift_x
    content_bottom = bottom + shift_y
    canvas_width = max(MIN_CANVAS_WIDTH, math.ceil(content_right + 50))
    legend_y = math.ceil(content_bottom + 55)
    canvas_height = legend_y + 78
    return shifted_boundary, canvas_width, canvas_height, legend_y


def render(view: dict) -> str:
    validate(view)
    if view["diagramType"] == "System Context":
        boxes, boundary, _ = layout_context(view)
    else:
        boxes, boundary, _ = layout_scoped(view)
    boundary, canvas_width, canvas_height, legend_y = fit_to_content(boxes, boundary)
    box_map = {box.id: box for box in boxes}
    require(all(r["source"] in box_map and r["destination"] in box_map for r in view["relationships"]), "all relationship endpoints must be rendered")
    for index, first in enumerate(boxes):
        for second in boxes[index + 1:]:
            require(not rects_overlap(box_rect(first), box_rect(second), 8), f"element boxes overlap: {first.id} and {second.id}")
    if boundary:
        boundary_rect = (boundary[0], boundary[1], boundary[0] + boundary[2], boundary[1] + boundary[3])
        for box in boxes:
            if box.inside_scope:
                rect = box_rect(box)
                require(
                    boundary_rect[0] < rect[0] and boundary_rect[1] < rect[1] and rect[2] < boundary_rect[2] and rect[3] < boundary_rect[3],
                    f"in-scope element lies outside scoped boundary: {box.id}",
                )
    routes = route_relationships(view["relationships"], box_map, canvas_width, legend_y - 20)
    place_relationship_labels(routes, boxes, canvas_width, legend_y - 16, boundary)

    title = escape(view["title"])
    subtitle = escape(view.get("description", ""))
    content = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="title desc" data-c4-key="Types are written in brackets; blue=in scope; grey=external; arrow=unidirectional relationship" data-c4-diagram-type="{escape(view['diagramType'])}">
<title id="title">{title}</title><desc id="desc">{subtitle}</desc><defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#394b59"/></marker></defs>
<style>
text{{font-family:Arial,sans-serif}}.diagram-title{{font-size:25px;font-weight:700;fill:#172033}}.diagram-description{{font-size:14px;fill:#52606d}}.boundary{{fill:#f4f8fc;stroke:#1168bd;stroke-width:2}}.boundary-label{{font-size:14px;font-weight:700;fill:#075ea8}}.element{{stroke-width:2}}.system{{fill:#1168bd;stroke:#084f91}}.container{{fill:#438dd5;stroke:#1f6fae}}.component{{fill:#85bbf0;stroke:#438dd5}}.person{{fill:#08427b;stroke:#052e56}}.external{{fill:#777;stroke:#555}}.code{{fill:#f5f6f7;stroke:#59636e}}.element-name{{font-size:17px;font-weight:700;text-anchor:middle;fill:white}}.element-type{{font-size:11px;text-anchor:middle;fill:white}}.element-description{{font-size:12px;text-anchor:middle;fill:white}}.element-tech{{font-size:10px;text-anchor:middle;fill:white}}.dark-text{{fill:#172033}}.relationship-halo{{stroke:white;stroke-width:7;fill:none;stroke-linejoin:round}}.relationship{{stroke:#394b59;stroke-width:2;fill:none;stroke-linejoin:round}}.relationship-label-bg{{fill:white;stroke:#d4d9dd;stroke-width:1}}.relationship-label{{font-size:12px;text-anchor:middle;fill:#172033}}.legend-text{{font-size:12px;fill:#34444f}}.legend-box{{stroke:#555;stroke-width:1}}
</style><text class="diagram-title" x="30" y="35">{title}</text><text class="diagram-description" x="30" y="58">{subtitle}</text>''']
    if boundary:
        x, y, w, h = boundary
        scope = view["scope"]
        scope_provenance = provenance_attributes(
            optional_string(scope, "modelElementId"),
            optional_string(scope, "modelBoundaryId"),
            reference_tuple(scope, "evidenceRefs"),
        )
        content.append(f'<g data-c4-element-id="{escape(scope["id"])}" data-c4-boundary="true"{scope_provenance}><rect class="boundary" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/><text class="boundary-label" x="{x+14}" y="{y+25}">{escape(scope["name"])} [{escape(scope["type"])}]</text></g>')
    for route in routes:
        content.append(render_relationship(route))
    content.extend(render_box(box) for box in boxes)
    content.append(f'<g aria-label="Diagram key"><text class="boundary-label" x="30" y="{legend_y}">Key</text><rect class="legend-box container" x="80" y="{legend_y-16}" width="32" height="20"/><text class="legend-text" x="120" y="{legend_y}">in-scope element</text><rect class="legend-box external" x="260" y="{legend_y-16}" width="32" height="20"/><text class="legend-text" x="300" y="{legend_y}">external element</text><line class="relationship" x1="430" y1="{legend_y-6}" x2="480" y2="{legend_y-6}" marker-end="url(#arrow)"/><text class="legend-text" x="490" y="{legend_y}">unidirectional relationship</text><text class="legend-text" x="80" y="{legend_y+30}">Element types are shown in [brackets]; relationship technology is shown in [brackets].</text></g>')
    content.append("</svg>")
    return "".join(content)


def html_page(view: dict, svg_name: str) -> str:
    navigation = view.get("navigation") or []
    crumbs = "<span aria-hidden=\"true\">›</span>".join(
        f'<a href="{escape(str(item["href"]))}">{escape(str(item["label"]))}</a>' for item in navigation
    )
    links = view.get("links") or []
    zoom = "".join(f'<a href="{escape(str(item["href"]))}">{escape(str(item["label"]))}</a>' for item in links)
    elements = [view["scope"], *view.get("elements", [])]
    element_rows = "".join(
        f'<tr><th scope="row">{escape(str(item["name"]))}</th><td>{escape(str(item["type"]))}</td>'
        f'<td>{escape(str(item.get("technology") or "—"))}</td><td>{escape(str(item["description"]))}</td></tr>'
        for item in elements
    )
    names = {item["id"]: item["name"] for item in elements}
    relationship_rows = "".join(
        f'<tr><td>{escape(str(item.get("order") or "—"))}</td><td>{escape(str(names.get(item["source"], item["source"])))}</td>'
        f'<td>{escape(str(names.get(item["destination"], item["destination"])))}</td><td>{escape(str(item["description"]))}</td>'
        f'<td>{escape(str(item.get("technology") or "—"))}</td></tr>'
        for item in view.get("relationships", [])
    )
    notes = view.get("notes") or []
    notes_section = "" if not notes else "<section><h2>Architecture notes</h2><ul>" + "".join(f"<li>{escape(str(note))}</li>" for note in notes) + "</ul></section>"
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(view['title'])}</title><style>
:root{{--ink:#172033;--muted:#52606d;--blue:#075ea8;--line:#d8e0e8;--panel:#fff;--wash:#f4f7fa}}*{{box-sizing:border-box}}html,body{{margin:0;min-height:100%}}body{{font:15px/1.55 Arial,sans-serif;color:var(--ink);background:var(--wash)}}main,nav{{width:min(1500px,calc(100% - 32px));margin:auto}}nav{{padding:18px 0 8px;display:flex;gap:9px;flex-wrap:wrap}}a{{color:var(--blue)}}header{{padding:18px 0 10px}}h1{{font-size:clamp(1.65rem,3vw,2.45rem);line-height:1.15;margin:0 0 10px}}h2{{margin:0 0 14px;font-size:1.25rem}}.lede{{max-width:85ch;color:var(--muted);font-size:1.05rem}}.meta{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}}.pill{{padding:5px 9px;border:1px solid #b9cee1;border-radius:999px;background:#eef6fc;font-size:.87rem;font-weight:700}}figure,section{{margin:18px 0;padding:18px;background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:0 2px 10px #1720330b}}figure{{padding:10px;overflow:auto}}figure img{{display:block;width:100%;min-width:850px;height:auto}}figcaption{{padding:10px 8px 2px;color:var(--muted)}}.links{{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}}.links a{{padding:9px 13px;background:#eef6fc;border:1px solid #b9cee1;border-radius:6px;text-decoration:none;font-weight:700}}.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}thead th{{background:#eef3f7;font-size:.88rem}}tbody th{{min-width:170px}}footer{{padding:18px 0 34px;color:var(--muted);font-size:.87rem}}@media(max-width:700px){{main,nav{{width:min(100% - 20px,1500px)}}section{{padding:12px}}}}
</style></head><body><nav aria-label="Breadcrumb">{crumbs}</nav><main><header><h1>{escape(view['title'])}</h1><p class="lede">{escape(str(view.get('description','')))}</p><div class="meta"><span class="pill">{escape(view['diagramType'])}</span><span class="pill">Scope: {escape(view['scope']['name'])}</span></div></header><div class="links">{zoom}</div><figure><img src="{escape(svg_name)}" alt="{escape(view['title'])}"><figcaption>Connected C4 view. Arrow labels describe direction and intent; bracketed text identifies element type or relationship technology.</figcaption></figure><section><h2>Elements and responsibilities</h2><div class="table-wrap"><table><thead><tr><th>Element</th><th>Type</th><th>Technology</th><th>Responsibility</th></tr></thead><tbody>{element_rows}</tbody></table></div></section><section><h2>Relationships</h2><div class="table-wrap"><table><thead><tr><th>Order</th><th>From</th><th>To</th><th>Intent</th><th>Technology</th></tr></thead><tbody>{relationship_rows}</tbody></table></div></section>{notes_section}<footer>Generated from a validated C4 view definition.</footer></main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("view", type=Path)
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    view = json.loads(args.view.read_text(encoding="utf-8"))
    svg = render(view)
    args.svg.parent.mkdir(parents=True, exist_ok=True)
    args.svg.write_text(svg, encoding="utf-8")
    if args.html:
        args.html.parent.mkdir(parents=True, exist_ok=True)
        relative_svg = Path(args.svg).resolve().relative_to(Path(args.html).resolve().parent) if Path(args.svg).resolve().is_relative_to(Path(args.html).resolve().parent) else Path(args.svg).resolve()
        args.html.write_text(html_page(view, str(relative_svg).replace("\\", "/")), encoding="utf-8")
    print(f"Rendered {args.svg}")
    if args.html:
        print(f"Wrote {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

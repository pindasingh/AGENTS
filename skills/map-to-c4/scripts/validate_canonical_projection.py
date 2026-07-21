#!/usr/bin/env python3
"""Validate that C4 view JSON remains traceable to a gathered canonical model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

STRICT_TYPES = {"System Context", "Container", "Dynamic"}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def reachable(starts: set[str], adjacency: dict[str, set[str]]) -> set[str]:
    visited = set(starts)
    pending = list(starts)
    while pending:
        current = pending.pop()
        for destination in adjacency.get(current, set()):
            if destination not in visited:
                visited.add(destination)
                pending.append(destination)
    return visited


def validate_view(model: dict[str, Any], view: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    diagram_type = view.get("diagramType")
    if diagram_type not in STRICT_TYPES:
        return failures
    nodes = model.get("nodes", {})
    model_relationships = model.get("relationships", {})
    boundaries = model.get("systemBoundaries", {})
    scope = view.get("scope", {})
    boundary_id = scope.get("modelBoundaryId")
    boundary = boundaries.get(boundary_id)
    if not boundary_id:
        failures.append(f"{label}: {diagram_type} scope.modelBoundaryId is required")
        boundary = None
    elif not boundary:
        failures.append(f"{label}: unknown model boundary {boundary_id}")
    elif boundary.get("status") != "confirmed":
        failures.append(f"{label}: boundary {boundary_id} is not confirmed")
    member_ids = set(boundary.get("members", [])) if boundary else set()

    endpoint_sets: dict[str, set[str]] = {scope.get("id", ""): member_ids}
    for index, element in enumerate(view.get("elements", [])):
        element_id = element.get("id")
        model_id = element.get("modelElementId")
        if not model_id:
            failures.append(f"{label}: elements[{index}].modelElementId is required")
            continue
        model_node = nodes.get(model_id)
        if model_node is None:
            failures.append(f"{label}: elements[{index}] references unknown model element {model_id}")
        if element_id:
            endpoint_sets[element_id] = {model_id}
        if diagram_type == "Container" and element.get("insideScope"):
            if boundary and model_id not in member_ids:
                failures.append(f"{label}: in-scope element {element_id} is not a member of {boundary_id}")
            if model_node:
                display_type = str(element.get("type", "")).lower()
                model_kind = model_node.get("kind")
                if model_kind == "runtime" and "container" not in display_type:
                    failures.append(f"{label}: runtime {model_id} must project as an Application Container")
                elif model_kind in {"store", "channel"} and not ("container" in display_type and ("store" in display_type or "database" in display_type)):
                    failures.append(f"{label}: {model_kind} {model_id} must project as a Data Store Container when included")
                elif model_kind not in {"runtime", "store", "channel"}:
                    failures.append(f"{label}: {model_kind} {model_id} cannot be an in-scope Container")
        elif diagram_type == "System Context" and model_node:
            display_type = str(element.get("type", "")).lower()
            if model_node.get("kind") == "person" and "person" not in display_type:
                failures.append(f"{label}: person {model_id} must project as a Person")
            elif model_node.get("kind") in {"runtime", "external"} and "software system" not in display_type:
                failures.append(f"{label}: machine dependency {model_id} must project as a Software System")
            elif model_node.get("kind") not in {"person", "runtime", "external"}:
                failures.append(f"{label}: {model_node.get('kind')} {model_id} cannot be a System Context supporting element")

    for index, relationship in enumerate(view.get("relationships", [])):
        where = f"{label}: relationships[{index}]"
        model_ids = relationship.get("modelRelationshipIds")
        if not isinstance(model_ids, list) or not model_ids or not all(isinstance(item, str) and item for item in model_ids):
            failures.append(f"{where}.modelRelationshipIds must be a non-empty string array")
            continue
        selected: list[dict[str, Any]] = []
        for model_id in model_ids:
            if model_id not in model_relationships:
                failures.append(f"{where} references unknown model relationship {model_id}")
            else:
                selected.append(model_relationships[model_id])
        source_set = endpoint_sets.get(relationship.get("source"), set())
        destination_set = endpoint_sets.get(relationship.get("destination"), set())
        if not source_set or not destination_set or not selected:
            continue
        adjacency: dict[str, set[str]] = {}
        reverse: dict[str, set[str]] = {}
        for item in selected:
            adjacency.setdefault(item["from"], set()).add(item["to"])
            reverse.setdefault(item["to"], set()).add(item["from"])
        forward = reachable(source_set, adjacency)
        backward = reachable(destination_set, reverse)
        if not (forward & destination_set):
            failures.append(f"{where} model relationships do not support the rendered direction")
            continue
        for item in selected:
            if item["from"] not in forward or item["to"] not in backward:
                failures.append(f"{where} includes model relationship outside the projected source-to-destination path")
                break
    return failures


def discover_views(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    for path in paths:
        if path.is_dir():
            result.extend(sorted(path.rglob("*.json")))
        else:
            result.append(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canonical", type=Path)
    parser.add_argument("views", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        model = read_json(args.canonical)
        failures: list[str] = []
        count = 0
        for path in discover_views(args.views):
            view = read_json(path)
            if "diagramType" not in view:
                continue
            count += 1
            failures.extend(validate_view(model, view, str(path)))
        if count == 0:
            failures.append("no C4 view JSON files found")
        if failures:
            print("Canonical projection validation failed:", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
        print(f"Validated {count} C4 view(s) against {args.canonical}")
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

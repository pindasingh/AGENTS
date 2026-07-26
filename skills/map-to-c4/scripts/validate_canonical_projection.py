#!/usr/bin/env python3
"""Validate C4 view provenance against a canonical architecture model.

System Context and Container views project first-class canonical nodes and
relationships. Component and Code views use explicit source-evidence references
for lower-level identities that the canonical discovery schema does not yet
model. Dynamic views may reuse either kind of identity, but every rendered item
must remain traceable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

DIAGRAM_TYPES = {"System Context", "Container", "Component", "Code", "Dynamic"}


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


def string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def evidence_refs(item: dict[str, Any]) -> list[str]:
    value = item.get("evidenceRefs")
    return value if string_list(value) else []


def display_kind(value: Any) -> str:
    lowered = str(value or "").strip().lower()
    if lowered == "person" or lowered.startswith("person:"):
        return "person"
    if lowered == "software system" or lowered.startswith("software system:"):
        return "software system"
    if lowered == "container" or lowered.startswith("container:"):
        return "container"
    if lowered == "component" or lowered.startswith("component:"):
        return "component"
    return "code"


def validate_model_projection(model_node: dict[str, Any], element: dict[str, Any], where: str, failures: list[str]) -> None:
    kind = model_node.get("kind")
    rendered = display_kind(element.get("type"))
    allowed = {
        "person": {"person"},
        "software system": {"runtime", "external"},
        "container": {"runtime", "store", "channel"},
    }
    if rendered in allowed and kind not in allowed[rendered]:
        failures.append(f"{where}: canonical {kind} cannot project as {element.get('type')}")
    if rendered == "container":
        display_type = str(element.get("type", "")).lower()
        data_store = "store" in display_type or "database" in display_type
        if kind == "runtime" and data_store:
            failures.append(f"{where}: canonical runtime must project as an Application Container")
        elif kind in {"store", "channel"} and not data_store:
            failures.append(f"{where}: canonical {kind} must project as a Data Store Container")
    if rendered in {"component", "code"}:
        failures.append(f"{where}: lower-level {rendered} identity must use evidenceRefs, not a canonical discovery node")


def confirmed_boundary(boundaries: dict[str, Any], boundary_id: Any, where: str, failures: list[str], required: bool) -> dict[str, Any] | None:
    if not boundary_id:
        if required:
            failures.append(f"{where}.modelBoundaryId is required")
        return None
    boundary = boundaries.get(boundary_id)
    if not isinstance(boundary, dict):
        failures.append(f"{where}: unknown model boundary {boundary_id}")
        return None
    if boundary.get("status") != "confirmed":
        failures.append(f"{where}: boundary {boundary_id} is not confirmed")
    return boundary


def validate_view(model: dict[str, Any], view: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    diagram_type = view.get("diagramType")
    if diagram_type not in DIAGRAM_TYPES:
        return [f"{label}: unsupported diagramType {diagram_type!r}"]

    nodes = model.get("nodes", {}) if isinstance(model.get("nodes"), dict) else {}
    model_relationships = model.get("relationships", {}) if isinstance(model.get("relationships"), dict) else {}
    boundaries = model.get("systemBoundaries", {}) if isinstance(model.get("systemBoundaries"), dict) else {}
    scope = view.get("scope", {}) if isinstance(view.get("scope"), dict) else {}
    scope_where = f"{label}: scope"

    boundary = confirmed_boundary(
        boundaries,
        scope.get("modelBoundaryId"),
        scope_where,
        failures,
        required=diagram_type in {"System Context", "Container", "Component"},
    )
    member_ids = set(boundary.get("members", [])) if boundary else set()

    scope_model_id = scope.get("modelElementId")
    scope_evidence = evidence_refs(scope)
    if diagram_type == "Component":
        if not scope_model_id:
            failures.append(f"{scope_where}.modelElementId is required for the scoped Container")
        elif scope_model_id not in nodes:
            failures.append(f"{scope_where} references unknown model element {scope_model_id}")
        else:
            validate_model_projection(nodes[scope_model_id], {**scope, "type": "Container"}, scope_where, failures)
            if boundary and scope_model_id not in member_ids:
                failures.append(f"{scope_where}: scoped Container {scope_model_id} is not a member of {scope.get('modelBoundaryId')}")
    elif diagram_type == "Code" and not scope_evidence:
        failures.append(f"{scope_where}.evidenceRefs is required for the scoped Component")
    elif diagram_type == "Dynamic" and not (scope.get("modelBoundaryId") or scope_model_id or scope_evidence):
        failures.append(f"{scope_where} requires modelBoundaryId, modelElementId, or evidenceRefs")

    if scope_model_id and diagram_type != "Component":
        if scope_model_id not in nodes:
            failures.append(f"{scope_where} references unknown model element {scope_model_id}")
        else:
            validate_model_projection(nodes[scope_model_id], scope, scope_where, failures)

    if scope.get("modelBoundaryId"):
        scope_set = member_ids
    elif scope_model_id in nodes:
        scope_set = {scope_model_id}
    else:
        scope_set = set()
    endpoint_sets: dict[str, set[str]] = {str(scope.get("id", "")): scope_set}

    elements = view.get("elements", []) if isinstance(view.get("elements"), list) else []
    for index, element in enumerate(elements):
        where = f"{label}: elements[{index}]"
        if not isinstance(element, dict):
            failures.append(f"{where} must be an object")
            continue
        element_id = element.get("id")
        model_id = element.get("modelElementId")
        refs = evidence_refs(element)
        if not model_id and not refs:
            failures.append(f"{where} requires modelElementId or evidenceRefs")
            continue
        model_node = nodes.get(model_id) if model_id else None
        if model_id and model_node is None:
            failures.append(f"{where} references unknown model element {model_id}")
        elif model_node:
            validate_model_projection(model_node, element, where, failures)

        if element_id:
            if model_node:
                endpoint_sets[str(element_id)] = {str(model_id)}
            elif diagram_type == "Component" and element.get("insideScope") and scope_model_id in nodes:
                # A component is a narrower evidenced part of its canonical runtime.
                endpoint_sets[str(element_id)] = {str(scope_model_id)}
            else:
                endpoint_sets[str(element_id)] = set()

        if diagram_type == "Container" and element.get("insideScope"):
            if boundary and model_id not in member_ids:
                failures.append(f"{where}: in-scope element {element_id} is not a member of {scope.get('modelBoundaryId')}")
            if not model_node:
                failures.append(f"{where}: in-scope Container requires a canonical modelElementId")
        elif diagram_type == "System Context" and refs:
            failures.append(f"{where}: System Context elements require canonical modelElementId provenance")
        elif diagram_type == "Component" and element.get("insideScope") and not refs:
            failures.append(f"{where}: in-scope Component requires source evidenceRefs")
        elif diagram_type == "Code" and not refs:
            failures.append(f"{where}: Code element requires source evidenceRefs")

    relationships = view.get("relationships", []) if isinstance(view.get("relationships"), list) else []
    for index, relationship in enumerate(relationships):
        where = f"{label}: relationships[{index}]"
        if not isinstance(relationship, dict):
            failures.append(f"{where} must be an object")
            continue
        model_ids = relationship.get("modelRelationshipIds")
        refs = evidence_refs(relationship)
        has_model_ids = string_list(model_ids)
        if not has_model_ids and not refs:
            failures.append(f"{where} requires modelRelationshipIds or evidenceRefs")
            continue
        if model_ids is not None and not has_model_ids:
            failures.append(f"{where}.modelRelationshipIds must be a non-empty string array")
            continue
        if not has_model_ids:
            continue

        selected: list[dict[str, Any]] = []
        for model_id in model_ids:
            if model_id not in model_relationships:
                failures.append(f"{where} references unknown model relationship {model_id}")
            else:
                selected.append(model_relationships[model_id])
        source_set = endpoint_sets.get(str(relationship.get("source")), set())
        destination_set = endpoint_sets.get(str(relationship.get("destination")), set())
        if not selected:
            continue
        if not source_set or not destination_set:
            failures.append(f"{where}: canonical relationship provenance requires canonically resolvable endpoints; use evidenceRefs for a lower-level relationship")
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
            print("C4 provenance validation failed:", file=sys.stderr)
            for failure in failures:
                print(f"- {failure}", file=sys.stderr)
            return 1
        print(f"Validated provenance for {count} C4 view(s) against {args.canonical}")
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Initialize, index, render, diff, and validate sharded architecture models."""

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

SCHEMA_VERSION = 2
ID = re.compile(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*")
SEQUENCE_NUMBER = re.compile(r"[1-9][0-9]*(?:\.[1-9][0-9]*)*")
CERTAINTIES = {"observed", "corroborated", "inferred", "conflicting", "unknown"}
NODE_KINDS = {"runtime", "store", "channel", "library", "external", "person"}
INTERFACE_KINDS = {"http", "grpc", "event", "message", "job", "ui", "file", "other"}
RELATIONSHIP_KINDS = {"request", "event", "message", "data", "search", "file", "library", "ui-load", "other"}
STEP_KINDS = {
    "entry", "local-operation", "interaction", "return", "decision", "data-read", "data-write",
    "config-read", "feature-evaluation", "publish", "deliver", "consume", "telemetry", "retry",
    "outcome", "gap",
}
BOUNDARIES = {
    "in-process", "runtime", "data-store", "search-store", "message-channel", "configuration",
    "observability", "external-service", "file", "other",
}
CONTINUATIONS = {"continue", "return", "terminate", "one-way", "unresolved"}
PATH_KINDS = {"success", "rejection", "no-result", "fallback", "retry", "failure", "asynchronous", "other"}
COVERAGE_STATUSES = {"complete", "partial", "blocked"}
INTERFACE_COVERAGE_STATUSES = {"covered", "excluded", "unresolved"}
SOURCE_STATUSES = {"pending", "scanning", "partial", "blocked", "complete"}
SOURCE_DOCUMENTS = {}
DISCOVERY_STATUSES = {"candidate", "accepted", "rejected", "unavailable"}

COLLECTION_LAYOUT = {
    "sources": ("sources", "scan.json"),
    "domains": ("domains", "*.json"),
    "nodes": ("nodes", "*.json"),
    "components": ("components", "*.json"),
    "interfaces": ("interfaces", "*.json"),
    "relationships": ("relationships", "*.json"),
    "gaps": ("gaps", "*.json"),
    "conflicts": ("conflicts", "*.json"),
}
INDEX_KEYS = {
    "schemaVersion", "generatedBy", "subjectRef", "decisionsRef", "progressRef", "artifacts",
    "hierarchy", "projections", "modelSemanticHash",
}
SET_LIKE_LIST_KEYS = {
    "aliases", "discoveryRoots", "requestedSources", "exclusions", "sourceIds", "componentIds",
    "operationIds", "pathIds", "triggerInterfaceIds", "ownerComponentIds", "continuesFromPathIds",
    "causedByPathIds", "callerRelationshipIds", "gapIds", "unresolvedGapIds", "knownOmissions",
    "technology", "rules", "included", "excluded", "limitations", "evidence", "sourceFindings",
    "discoveredRepositories", "searches", "alternatives", "callers",
}


def normalized(value, parent_key=None):
    if isinstance(value, dict):
        return {key: normalized(child, key) for key, child in sorted(value.items())}
    if isinstance(value, list):
        items = [normalized(child) for child in value]
        if parent_key in SET_LIKE_LIST_KEYS:
            return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
        return items
    return value


def canonical_bytes(value):
    return (json.dumps(normalized(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def read_json(path, failures=None):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        if failures is None:
            raise ValueError(f"{path}: {error}") from error
        failures.append(f"{path}: {error}")
        return None
    return value


def digest_bytes(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_json(value):
    return digest_bytes(canonical_bytes(value))


def slug(value):
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result or "unnamed"


def valid_id(value, prefix=None):
    return isinstance(value, str) and bool(ID.fullmatch(value)) and (prefix is None or value.startswith(prefix + "."))


def long_path(path):
    resolved = str(path.resolve())
    if sys.platform == "win32" and not resolved.startswith("\\\\?\\"):
        resolved = "\\\\?\\" + resolved
    return Path(resolved)


def relative(root, path):
    return path.relative_to(root).as_posix()


def semantic_value(document, collection):
    """Remove provenance-only material while retaining architecture semantics."""
    value = deepcopy(document)

    def strip_provenance(item):
        if isinstance(item, dict):
            return {
                key: strip_provenance(child)
                for key, child in item.items()
                if key not in {"evidence", "sourceFindings"}
            }
        if isinstance(item, list):
            return [strip_provenance(child) for child in item]
        return item

    value = strip_provenance(value)
    if collection == "sources" and isinstance(value, dict):
        source = value.get("source")
        if isinstance(source, dict):
            for key in ("location", "repository", "revision", "branch"):
                source.pop(key, None)
    if collection == "domains" and isinstance(value, dict):
        value.pop("sourceIds", None)
    if collection == "controls" and isinstance(value, dict) and isinstance(value.get("subject"), dict):
        value["subject"].pop("discoveryRoots", None)
        value["subject"].pop("requestedSources", None)
    return value


def artifact_entry(root, path, document, collection):
    return {
        "path": relative(root, path),
        "semanticHash": digest_json(semantic_value(document, collection)),
        "contentHash": digest_json(document),
    }


def discover_artifacts(root, failures=None):
    artifacts = {name: {} for name in (*COLLECTION_LAYOUT, "operations", "paths")}
    documents = {name: {} for name in artifacts}

    for collection, (directory, pattern) in COLLECTION_LAYOUT.items():
        base = root / directory
        paths = sorted(base.glob(f"*/{pattern}" if collection == "sources" else pattern)) if base.exists() else []
        for path in paths:
            document = read_json(path, failures)
            if not isinstance(document, dict):
                continue
            artifact_id = document.get("id")
            if not isinstance(artifact_id, str):
                if failures is not None:
                    failures.append(f"{path}: artifact requires an id")
                continue
            if artifact_id in artifacts[collection]:
                if failures is not None:
                    failures.append(f"{path}: duplicate artifact id {artifact_id}")
                continue
            artifacts[collection][artifact_id] = artifact_entry(root, path, document, collection)
            documents[collection][artifact_id] = document

    operations_root = root / "operations"
    if operations_root.exists():
        for path in sorted(operations_root.glob("*/operation.json")):
            document = read_json(path, failures)
            if isinstance(document, dict) and isinstance(document.get("id"), str):
                artifact_id = document["id"]
                if artifact_id in artifacts["operations"]:
                    if failures is not None:
                        failures.append(f"{path}: duplicate artifact id {artifact_id}")
                    continue
                artifacts["operations"][artifact_id] = artifact_entry(root, path, document, "operations")
                documents["operations"][artifact_id] = document
        for path in sorted(operations_root.glob("*/paths/*.json")):
            document = read_json(path, failures)
            if isinstance(document, dict) and isinstance(document.get("id"), str):
                artifact_id = document["id"]
                if artifact_id in artifacts["paths"]:
                    if failures is not None:
                        failures.append(f"{path}: duplicate artifact id {artifact_id}")
                    continue
                artifacts["paths"][artifact_id] = artifact_entry(root, path, document, "paths")
                documents["paths"][artifact_id] = document
    return artifacts, documents


def projection_entries(root, documents):
    result = {}
    for path_id, path_document in sorted(documents["paths"].items()):
        operation_id = path_document.get("operationId", "unknown")
        projection_root = root / "projections" / operation_id / path_id
        entries = {}
        for name in ("numbered-sequence.md", "sequence-diagram.txt"):
            path = projection_root / name
            if path.is_file():
                entries[name] = {
                    "path": relative(root, path),
                    "contentHash": digest_bytes(path.read_bytes()),
                }
        result[path_id] = entries
    return result


def build_index_value(root, failures=None):
    artifacts, documents = discover_artifacts(root, failures)
    hierarchy = {"domains": {}, "operations": {}}
    for domain_id, domain in sorted(documents["domains"].items()):
        hierarchy["domains"][domain_id] = {
            "componentIds": domain.get("componentIds", []),
            "operationIds": domain.get("operationIds", []),
            "sourceIds": domain.get("sourceIds", []),
        }
    for operation_id, operation in sorted(documents["operations"].items()):
        hierarchy["operations"][operation_id] = {
            "domainId": operation.get("domainId"),
            "ownerComponentIds": operation.get("ownerComponentIds", []),
            "pathIds": operation.get("pathIds", []),
            "triggerInterfaceIds": operation.get("triggerInterfaceIds", []),
        }
    controls = {}
    semantic_records = []
    for name in ("subject.json", "decisions.json", "progress.json"):
        path = root / name
        document = read_json(path, failures)
        if isinstance(document, dict):
            controls[name] = artifact_entry(root, path, document, "controls")
    for name in ("subject.json", "decisions.json"):
        if name in controls:
            semantic_records.append(["control", name, controls[name]["semanticHash"]])
    for collection in ("domains", "nodes", "components", "interfaces", "relationships", "operations", "paths", "gaps", "conflicts"):
        for artifact_id, entry in sorted(artifacts[collection].items()):
            semantic_records.append([collection, artifact_id, entry["semanticHash"]])
    return normalized({
        "schemaVersion": SCHEMA_VERSION,
        "generatedBy": "architecture_model.py",
        "subjectRef": controls.get("subject.json"),
        "decisionsRef": controls.get("decisions.json"),
        "progressRef": controls.get("progress.json"),
        "artifacts": artifacts,
        "hierarchy": hierarchy,
        "projections": projection_entries(root, documents),
        "modelSemanticHash": digest_json(semantic_records),
    })


def build_index(root):
    index = build_index_value(root)
    write_json(root / "index.json", index)
    return index


def hierarchy_key(number):
    return tuple(int(part) for part in number.split("."))


def display_label(step):
    return step.get("name") if step.get("kind") == "stage" else step.get("operation")


def safe_text(value):
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def caller_endpoints(path_document, step):
    caller_map = {
        caller.get("relationshipId"): caller.get("nodeId")
        for caller in path_document.get("callers", [])
        if isinstance(caller, dict)
    }
    return [caller_map.get(relationship_id) for relationship_id in step.get("callerRelationshipIds", [])]


def step_endpoints(path_document, step):
    if step.get("kind") == "stage":
        return None
    if "at" in step:
        return [step["at"]], [step["at"]]
    if "source" in step and "destination" in step:
        return [step["source"]], [step["destination"]]
    callers = caller_endpoints(path_document, step)
    if "destination" in step:
        return callers, [step["destination"]]
    if "source" in step:
        return [step["source"]], callers
    return [], []


def annotation(step):
    values = [
        ("kind", step.get("kind")),
        ("boundary", step.get("boundary")),
        ("input", step.get("input")),
        ("output", step.get("output")),
        ("relationship", step.get("relationshipId")),
        ("interface", step.get("interfaceId")),
        ("continuation", step.get("continuation")),
        ("certainty", step.get("certainty")),
    ]
    return "; ".join(f"{name}={safe_text(value)}" for name, value in values if value is not None)


def render_numbered(path_document):
    participant_ids = [participant["id"] for participant in path_document.get("participants", [])]
    callers = [caller["nodeId"] for caller in path_document.get("callers", [])]
    outcome = path_document.get("outcome", {})
    coverage = path_document.get("coverage", {})
    lines = [
        f"# {safe_text(path_document.get('name', ''))}",
        "",
        f"- Path ID: `{path_document.get('id', '')}`",
        f"- Operation ID: `{path_document.get('operationId', '')}`",
        f"- Path kind: {path_document.get('kind', '')}",
        f"- Trigger interface IDs: {' | '.join(path_document.get('triggerInterfaceIds', []))}",
        f"- Evidenced callers: {' | '.join(callers) if callers else 'none'}",
        f"- Participant IDs: {' | '.join(participant_ids)}",
        f"- Outcome: {outcome.get('at', '')} — {safe_text(outcome.get('description', ''))}",
        f"- Coverage: {coverage.get('status', '')}",
        "",
        "## Numbered execution",
        "",
    ]
    for step in path_document.get("sequence", []):
        number = step.get("number", "?")
        label = safe_text(display_label(step) or "")
        indent = "  " * max(0, number.count("."))
        lines.append(f"{indent}{number}. **{label}**")
        if step.get("kind") != "stage":
            endpoints = step_endpoints(path_document, step)
            source = "|".join(endpoints[0]) if endpoints else ""
            destination = "|".join(endpoints[1]) if endpoints else ""
            lines.append(f"{indent}   - Execution: `{source} -> {destination}`")
            lines.append(f"{indent}   - {annotation(step)}")
            evidence = step.get("evidence", [])
            summary = " | ".join(
                f"{item.get('sourceId', '?')}:{item.get('path', '?')} — {safe_text(item.get('observation', ''))}"
                for item in evidence if isinstance(item, dict)
            )
            lines.append(f"{indent}   - Evidence: {summary}")
    unresolved = coverage.get("unresolvedGapIds", [])
    omissions = coverage.get("knownOmissions", [])
    lines.extend([
        "",
        "## Unresolved points and omissions",
        "",
        f"- Gap IDs: {' | '.join(unresolved) if unresolved else 'none'}",
        f"- Known omissions: {' | '.join(omissions) if omissions else 'none'}",
        "",
    ])
    return "\n".join(lines)


def render_ascii(path_document):
    participants = path_document.get("participants", [])
    aliases = {participant["id"]: f"P{index}" for index, participant in enumerate(participants, start=1)}
    outcome = path_document.get("outcome", {})
    coverage = path_document.get("coverage", {})
    lines = [
        f"Path: {safe_text(path_document.get('name', ''))}",
        f"Path ID: {path_document.get('id', '')}",
        f"Operation ID: {path_document.get('operationId', '')}",
        f"Path kind: {path_document.get('kind', '')}",
        f"Trigger interface IDs: {' | '.join(path_document.get('triggerInterfaceIds', []))}",
        f"Coverage: {coverage.get('status', '')}",
        "",
        "Participants (exact path set):",
    ]
    for index, participant in enumerate(participants, start=1):
        lines.append(f"  P{index} {participant['id']} : {safe_text(participant.get('role', ''))}")
    lines.append("")
    for step in path_document.get("sequence", []):
        number = step.get("number", "?")
        label = safe_text(display_label(step) or "")
        if step.get("kind") == "stage":
            lines.append(f"{number} [STAGE] {label}")
            continue
        source_ids, destination_ids = step_endpoints(path_document, step)
        source = "|".join(aliases.get(item, "?") for item in source_ids)
        destination = "|".join(aliases.get(item, "?") for item in destination_ids)
        lines.append(f"{number} {source} -> {destination} : {label} [{annotation(step)}]")
    unresolved = coverage.get("unresolvedGapIds", [])
    lines.extend([
        "",
        f"Outcome: {outcome.get('at', '')} — {safe_text(outcome.get('description', ''))}",
        f"Unresolved gap IDs: {' | '.join(unresolved) if unresolved else 'none'}",
        "",
    ])
    return "\n".join(lines)


def render(root, selected_path_id=None):
    _, documents = discover_artifacts(root)
    rendered = 0
    for path_id, path_document in sorted(documents["paths"].items()):
        if selected_path_id and path_id != selected_path_id:
            continue
        operation_id = path_document.get("operationId")
        if not operation_id:
            raise ValueError(f"{path_id}: missing operationId")
        destination = root / "projections" / operation_id / path_id
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "numbered-sequence.md").write_text(render_numbered(path_document), encoding="utf-8", newline="\n")
        (destination / "sequence-diagram.txt").write_text(render_ascii(path_document), encoding="utf-8", newline="\n")
        rendered += 1
    build_index(root)
    return rendered


def require_object(document, path, failures):
    if not isinstance(document, dict):
        failures.append(f"{path}: must be an object")
        return False
    if document.get("schemaVersion") != SCHEMA_VERSION:
        failures.append(f"{path}: schemaVersion must be {SCHEMA_VERSION}")
        return False
    return True


def check_keys(document, required, optional, label, failures):
    if not isinstance(document, dict):
        failures.append(f"{label}: must be an object")
        return
    missing = required - set(document)
    extras = set(document) - required - optional
    if missing:
        failures.append(f"{label}: missing keys {sorted(missing)}")
    if extras:
        failures.append(f"{label}: undocumented keys {sorted(extras)}")


def require_list(value, label, failures, non_empty=False):
    if not isinstance(value, list) or (non_empty and not value):
        failures.append(f"{label}: must be {'a non-empty' if non_empty else 'an'} array")
        return []
    return value


def require_string(value, label, failures):
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{label}: must be a non-empty string")
        return False
    return True


def validate_evidence(evidence, label, source_ids, failures, required=True):
    values = require_list(evidence, label, failures, non_empty=required)
    for index, item in enumerate(values):
        item_label = f"{label}[{index}]"
        check_keys(item, {"sourceId", "path", "observation"}, {"symbol", "lineStart", "lineEnd"}, item_label, failures)
        if not isinstance(item, dict):
            continue
        if item.get("sourceId") not in source_ids:
            failures.append(f"{item_label}: sourceId does not resolve")
        require_string(item.get("path"), f"{item_label}.path", failures)
        require_string(item.get("observation"), f"{item_label}.observation", failures)
        if ("lineStart" in item) != ("lineEnd" in item):
            failures.append(f"{item_label}: lineStart and lineEnd must appear together")
        if "lineStart" in item:
            start, end = item.get("lineStart"), item.get("lineEnd")
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start:
                failures.append(f"{item_label}: invalid line range")


def validate_findings(findings, label, source_ids, failures, required=True):
    values = require_list(findings, label, failures, non_empty=required)
    allowed = {"sourceId", "unitId", "componentId", "interfaceId", "outboundId", "operationId", "stepOrder"}
    for index, item in enumerate(values):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict):
            failures.append(f"{item_label}: must be an object")
            continue
        if set(item) - allowed or "sourceId" not in item:
            failures.append(f"{item_label}: invalid source-finding shape")
        source_id = item.get("sourceId")
        scan = SOURCE_DOCUMENTS.get(source_id)
        if source_id not in source_ids or not scan:
            failures.append(f"{item_label}: sourceId does not resolve")
            continue
        units = scan.get("units", {}) if isinstance(scan.get("units"), dict) else {}
        components = scan.get("components", {}) if isinstance(scan.get("components"), dict) else {}
        operations = scan.get("operations", {}) if isinstance(scan.get("operations"), dict) else {}
        unit_id, component_id, operation_id = item.get("unitId"), item.get("componentId"), item.get("operationId")
        if unit_id is not None and unit_id not in units:
            failures.append(f"{item_label}.unitId: does not resolve in {source_id}")
        if component_id is not None and component_id not in components:
            failures.append(f"{item_label}.componentId: does not resolve in {source_id}")
        if operation_id is not None and operation_id not in operations:
            failures.append(f"{item_label}.operationId: does not resolve in {source_id}")
        if "stepOrder" in item:
            operation = operations.get(operation_id, {}) if operation_id else {}
            orders = {
                step.get("order") for step in operation.get("steps", []) if isinstance(step, dict)
            } if isinstance(operation, dict) else set()
            if item.get("stepOrder") not in orders:
                failures.append(f"{item_label}.stepOrder: does not resolve in {source_id}:{operation_id}")
        if "interfaceId" in item:
            interface_ids = {
                interface.get("id")
                for unit in units.values() if isinstance(unit, dict)
                for interface in unit.get("inbound", []) if isinstance(interface, dict)
            }
            if item.get("interfaceId") not in interface_ids:
                failures.append(f"{item_label}.interfaceId: does not resolve in {source_id}")
        if "outboundId" in item:
            outbound_ids = {
                outbound.get("id")
                for unit in units.values() if isinstance(unit, dict)
                for outbound in unit.get("outbound", []) if isinstance(outbound, dict)
            }
            if item.get("outboundId") not in outbound_ids:
                failures.append(f"{item_label}.outboundId: does not resolve in {source_id}")


def validate_common_claim(document, label, source_ids, failures):
    if document.get("certainty") not in CERTAINTIES:
        failures.append(f"{label}.certainty: invalid value")
    validate_findings(document.get("sourceFindings"), f"{label}.sourceFindings", source_ids, failures)
    validate_evidence(document.get("evidence"), f"{label}.evidence", source_ids, failures)


def validate_sequence(path_id, path_document, all_elements, interfaces, relationships, gaps, source_ids, failures):
    sequence = require_list(path_document.get("sequence"), f"{path_id}.sequence", failures, non_empty=True)
    participant_records = require_list(path_document.get("participants"), f"{path_id}.participants", failures, non_empty=True)
    participants = []
    for index, participant in enumerate(participant_records):
        label = f"{path_id}.participants[{index}]"
        check_keys(participant, {"id", "role"}, set(), label, failures)
        if isinstance(participant, dict):
            participants.append(participant.get("id"))
            if participant.get("id") not in all_elements:
                failures.append(f"{label}.id: does not resolve")
            require_string(participant.get("role"), f"{label}.role", failures)
    if len(participants) != len(set(participants)):
        failures.append(f"{path_id}: duplicate participants")

    callers = require_list(path_document.get("callers"), f"{path_id}.callers", failures)
    caller_relationships = {}
    caller_nodes = set()
    trigger_ids = set(path_document.get("triggerInterfaceIds", []))
    trigger_owners = {interfaces[item].get("ownerNodeId") for item in trigger_ids if item in interfaces}
    for index, caller in enumerate(callers):
        label = f"{path_id}.callers[{index}]"
        check_keys(caller, {"nodeId", "relationshipId", "certainty", "sourceFindings", "evidence"}, set(), label, failures)
        if not isinstance(caller, dict):
            continue
        node_id, relationship_id = caller.get("nodeId"), caller.get("relationshipId")
        caller_nodes.add(node_id)
        caller_relationships[relationship_id] = node_id
        relationship = relationships.get(relationship_id)
        if (
            not relationship
            or relationship.get("fromId") != node_id
            or relationship.get("toId") not in trigger_owners
            or relationship.get("interfaceId") not in trigger_ids
        ):
            failures.append(f"{label}: caller relationship direction/target/interface is incompatible with the trigger")
        if caller.get("certainty") not in CERTAINTIES:
            failures.append(f"{label}.certainty: invalid value")
        validate_findings(caller.get("sourceFindings"), f"{label}.sourceFindings", source_ids, failures)
        validate_evidence(caller.get("evidence"), f"{label}.evidence", source_ids, failures)

    numbers, touched, touched_order = [], set(), []
    sibling_numbers = {}
    for index, step in enumerate(sequence):
        label = f"{path_id}.sequence[{index}]"
        if not isinstance(step, dict):
            failures.append(f"{label}: must be an object")
            continue
        number = step.get("number")
        if not isinstance(number, str) or not SEQUENCE_NUMBER.fullmatch(number):
            failures.append(f"{label}.number: invalid hierarchical sequence number")
            continue
        numbers.append(number)
        expected_parent = number.rsplit(".", 1)[0] if "." in number else None
        if step.get("parent") != expected_parent:
            failures.append(f"{label}.parent: expected {expected_parent!r}")
        if expected_parent and expected_parent not in numbers:
            failures.append(f"{label}: parent must appear first")
        sibling_numbers.setdefault(expected_parent or "", []).append(int(number.rsplit(".", 1)[-1]))
        kind = step.get("kind")
        if expected_parent is None and kind != "stage":
            failures.append(f"{label}: root sequence records must be stages")
        if kind == "stage":
            check_keys(step, {"number", "kind", "name", "sourceFindings", "evidence"}, set(), label, failures)
            require_string(step.get("name"), f"{label}.name", failures)
            validate_findings(step.get("sourceFindings"), f"{label}.sourceFindings", source_ids, failures)
            validate_evidence(step.get("evidence"), f"{label}.evidence", source_ids, failures)
            continue
        if kind not in STEP_KINDS:
            failures.append(f"{label}.kind: invalid value")
        required = {
            "number", "parent", "kind", "operation", "input", "output", "boundary", "continuation",
            "certainty", "sourceFindings", "evidence",
        }
        optional = {"at", "source", "destination", "callerRelationshipIds", "relationshipId", "interfaceId", "gapIds"}
        check_keys(step, required, optional, label, failures)
        for field in ("operation", "input", "output"):
            require_string(step.get(field), f"{label}.{field}", failures)
        if step.get("boundary") not in BOUNDARIES:
            failures.append(f"{label}.boundary: invalid value")
        if step.get("continuation") not in CONTINUATIONS:
            failures.append(f"{label}.continuation: invalid value")
        if step.get("certainty") not in CERTAINTIES:
            failures.append(f"{label}.certainty: invalid value")
        validate_findings(step.get("sourceFindings"), f"{label}.sourceFindings", source_ids, failures)
        validate_evidence(step.get("evidence"), f"{label}.evidence", source_ids, failures)
        forms = [
            "at" in step,
            "source" in step and "destination" in step,
            "callerRelationshipIds" in step and "destination" in step and "source" not in step,
            "callerRelationshipIds" in step and "source" in step and "destination" not in step,
        ]
        if sum(forms) != 1:
            failures.append(f"{label}: requires exactly one execution form")
        endpoints = step_endpoints(path_document, step)
        if endpoints:
            for endpoint in (*endpoints[0], *endpoints[1]):
                touched.add(endpoint)
                if endpoint not in touched_order:
                    touched_order.append(endpoint)
                if endpoint not in all_elements:
                    failures.append(f"{label}: endpoint {endpoint!r} does not resolve")
        relationship_id = step.get("relationshipId")
        if relationship_id:
            relationship = relationships.get(relationship_id)
            if not relationship:
                failures.append(f"{label}.relationshipId: does not resolve")
            elif endpoints and not relationship_compatible(relationship, endpoints[0], endpoints[1], all_elements):
                failures.append(f"{label}.relationshipId: direction is incompatible with step endpoints")
        interface_id = step.get("interfaceId")
        if interface_id not in interfaces and interface_id is not None:
            failures.append(f"{label}.interfaceId: does not resolve")
        for relationship in step.get("callerRelationshipIds", []):
            if relationship not in caller_relationships:
                failures.append(f"{label}.callerRelationshipIds: {relationship!r} is not a path caller")
        for gap_id in step.get("gapIds", []):
            if gap_id not in gaps:
                failures.append(f"{label}.gapIds: {gap_id!r} does not resolve")

    if len(numbers) != len(set(numbers)):
        failures.append(f"{path_id}: sequence numbers must be unique")
    if numbers != sorted(numbers, key=hierarchy_key):
        failures.append(f"{path_id}: sequence must be in hierarchical numeric order")
    for parent, values in sibling_numbers.items():
        if values != list(range(1, len(values) + 1)):
            failures.append(f"{path_id}: sibling numbers under {parent or 'root'} are not contiguous")
    if set(participants) != touched:
        failures.append(f"{path_id}: participants must exactly equal touched sequence elements")
    if participants != touched_order:
        failures.append(f"{path_id}: participants must follow first endpoint appearance order")
    if not caller_nodes <= set(participants):
        failures.append(f"{path_id}: every caller must be a participant")

    outcome = path_document.get("outcome")
    check_keys(outcome, {"kind", "at", "description"}, set(), f"{path_id}.outcome", failures)
    if isinstance(outcome, dict):
        if outcome.get("at") not in numbers:
            failures.append(f"{path_id}.outcome.at: does not resolve")
        require_string(outcome.get("description"), f"{path_id}.outcome.description", failures)
        matching = next((step for step in sequence if isinstance(step, dict) and step.get("number") == outcome.get("at")), None)
        if not matching or matching.get("continuation") not in {"return", "terminate", "one-way", "unresolved"}:
            failures.append(f"{path_id}.outcome.at: must reference a terminal step")

    coverage = path_document.get("coverage")
    check_keys(coverage, {"status", "unresolvedGapIds", "knownOmissions"}, set(), f"{path_id}.coverage", failures)
    if isinstance(coverage, dict):
        if coverage.get("status") not in COVERAGE_STATUSES:
            failures.append(f"{path_id}.coverage.status: invalid value")
        unresolved = require_list(coverage.get("unresolvedGapIds"), f"{path_id}.coverage.unresolvedGapIds", failures)
        require_list(coverage.get("knownOmissions"), f"{path_id}.coverage.knownOmissions", failures)
        for gap_id in unresolved:
            if gap_id not in gaps:
                failures.append(f"{path_id}.coverage: unresolved gap {gap_id!r} does not resolve")
        if coverage.get("status") == "complete" and (unresolved or coverage.get("knownOmissions")):
            failures.append(f"{path_id}.coverage: complete paths cannot have unresolved gaps or omissions")


def runtime_owner(element_id, all_elements):
    element = all_elements.get(element_id, {})
    return element.get("ownerNodeId", element_id)


def relationship_compatible(relationship, source_ids, destination_ids, all_elements):
    sources = {runtime_owner(item, all_elements) for item in source_ids}
    destinations = {runtime_owner(item, all_elements) for item in destination_ids}
    return relationship.get("fromId") in sources and relationship.get("toId") in destinations


def validate_source_scan(source_id, scan, label, failures):
    check_keys(
        scan,
        {"schemaVersion", "id", "source", "discoveredRepositories", "units", "components", "operations", "gaps"},
        set(), label, failures,
    )
    if scan.get("id") != source_id or not valid_id(source_id, "source"):
        failures.append(f"{label}.id: invalid source ID")
    source = scan.get("source")
    check_keys(source, {"location", "repository", "revision", "branch", "status", "coverage"}, set(), f"{label}.source", failures)
    if isinstance(source, dict):
        require_string(source.get("location"), f"{label}.source.location", failures)
        if source.get("status") not in SOURCE_STATUSES:
            failures.append(f"{label}.source.status: invalid value")
        coverage = source.get("coverage")
        check_keys(coverage, {"included", "excluded", "limitations"}, set(), f"{label}.source.coverage", failures)
    candidates = require_list(scan.get("discoveredRepositories"), f"{label}.discoveredRepositories", failures)
    for index, candidate in enumerate(candidates):
        item_label = f"{label}.discoveredRepositories[{index}]"
        check_keys(candidate, {"id", "location", "reason", "status", "evidence"}, {"repository"}, item_label, failures)
        if isinstance(candidate, dict) and candidate.get("status") not in DISCOVERY_STATUSES:
            failures.append(f"{item_label}.status: invalid value")


def validate(root, allow_incomplete=False):
    global SOURCE_DOCUMENTS
    failures = []
    top_documents = {}
    for name in ("subject.json", "decisions.json", "progress.json", "index.json"):
        path = root / name
        document = read_json(path, failures)
        top_documents[name] = document
        require_object(document, path, failures)

    artifacts, documents = discover_artifacts(root, failures)
    SOURCE_DOCUMENTS = documents["sources"]
    source_ids = set(documents["sources"])
    node_ids = set(documents["nodes"])
    component_ids = set(documents["components"])
    all_elements = {**documents["nodes"], **documents["components"]}
    for collection, entries in artifacts.items():
        for artifact_id, entry in entries.items():
            if collection == "sources":
                expected_path = f"sources/{artifact_id}/scan.json"
            elif collection == "operations":
                expected_path = f"operations/{artifact_id}/operation.json"
            elif collection == "paths":
                operation_id = documents["paths"][artifact_id].get("operationId")
                expected_path = f"operations/{operation_id}/paths/{artifact_id}.json"
            else:
                expected_path = f"{collection}/{artifact_id}.json"
            if entry["path"] != expected_path:
                failures.append(f"{entry['path']}: artifact path must be {expected_path}")
            document = documents[collection][artifact_id]
            expected_prefix = {
                "sources": "source", "domains": "domain", "components": "component", "interfaces": "interface",
                "relationships": "relationship", "operations": "operation", "paths": "path", "gaps": "gap",
                "conflicts": "conflict",
            }.get(collection)
            if document.get("id") != artifact_id or not valid_id(artifact_id, expected_prefix):
                failures.append(f"{entry['path']}: artifact ID is invalid or differs from its key")

    subject = top_documents.get("subject.json") or {}
    check_keys(subject, {"schemaVersion", "subject"}, set(), "subject.json", failures)
    subject_record = subject.get("subject")
    check_keys(
        subject_record,
        {"id", "name", "description", "aliases", "discoveryRoots", "requestedSources", "exclusions"},
        set(), "subject.json.subject", failures,
    )
    if isinstance(subject_record, dict):
        if not valid_id(subject_record.get("id"), "domain"):
            failures.append("subject.json.subject.id: must be a domain.* ID")
        elif subject_record.get("id") not in documents["domains"]:
            failures.append("subject.json.subject.id: does not resolve to a domain shard")
        for field in ("aliases", "discoveryRoots", "requestedSources", "exclusions"):
            require_list(subject_record.get(field), f"subject.json.subject.{field}", failures)
        if set(subject_record.get("requestedSources", [])) != source_ids:
            failures.append("subject.json.subject.requestedSources: must exactly match source artifacts")

    decisions = top_documents.get("decisions.json") or {}
    check_keys(
        decisions,
        {"schemaVersion", "identityOverrides", "targetOverrides", "repositoryOverrides", "systemBoundaries"},
        set(), "decisions.json", failures,
    )
    for field in ("identityOverrides", "targetOverrides", "repositoryOverrides", "systemBoundaries"):
        if not isinstance(decisions.get(field), dict):
            failures.append(f"decisions.json.{field}: must be an object")
    for boundary_id, boundary in (decisions.get("systemBoundaries") or {}).items():
        label = f"decisions.json.systemBoundaries.{boundary_id}"
        check_keys(boundary, {"name", "responsibility", "status", "members", "evidence"}, set(), label, failures)
        if not valid_id(boundary_id, "system"):
            failures.append(f"{label}: invalid boundary ID")
        if isinstance(boundary, dict):
            if boundary.get("status") not in {"candidate", "confirmed", "rejected", "conflicting"}:
                failures.append(f"{label}.status: invalid value")
            for member in require_list(boundary.get("members"), f"{label}.members", failures):
                if member not in node_ids:
                    failures.append(f"{label}.members: {member!r} does not resolve")
            require_list(boundary.get("evidence"), f"{label}.evidence", failures, non_empty=True)

    progress = top_documents.get("progress.json") or {}
    check_keys(progress, {"schemaVersion", "activeSourceId", "sources", "pathReviews"}, set(), "progress.json", failures)
    progress_sources = progress.get("sources", {}) if isinstance(progress.get("sources"), dict) else {}
    if set(progress_sources) != source_ids:
        failures.append("progress.json.sources: must exactly match source artifacts")
    if progress.get("activeSourceId") is not None and progress.get("activeSourceId") not in source_ids:
        failures.append("progress.json.activeSourceId: does not resolve")
    for source_id, scan in documents["sources"].items():
        validate_source_scan(source_id, scan, artifacts["sources"][source_id]["path"], failures)
        ledger = progress_sources.get(source_id, {})
        required_gates = {"scanWritten", "scanValidated", "graphUpdated", "gapsReviewed", "conflictsReviewed"}
        check_keys(ledger, {"stage", "gates"}, {"revision"}, f"progress.sources.{source_id}", failures)
        gates = ledger.get("gates", {}) if isinstance(ledger, dict) else {}
        if set(gates) != required_gates:
            failures.append(f"progress.sources.{source_id}.gates: invalid gate set")
        if not allow_incomplete:
            if ledger.get("stage") != "complete" or not all(gates.values()):
                failures.append(f"progress.sources.{source_id}: source is not complete")
            scan_revision = scan.get("source", {}).get("revision")
            if not scan_revision or ledger.get("revision") != scan_revision:
                failures.append(f"progress.sources.{source_id}: revision does not match scan")

    for domain_id, document in documents["domains"].items():
        label = artifacts["domains"][domain_id]["path"]
        check_keys(
            document,
            {"schemaVersion", "id", "name", "description", "sourceIds", "componentIds", "operationIds"},
            set(), label, failures,
        )
        if not valid_id(domain_id, "domain") or document.get("id") != domain_id:
            failures.append(f"{label}.id: invalid domain ID")
        for source_id in require_list(document.get("sourceIds"), f"{label}.sourceIds", failures):
            if source_id not in source_ids:
                failures.append(f"{label}.sourceIds: {source_id!r} does not resolve")
        for component_id in require_list(document.get("componentIds"), f"{label}.componentIds", failures):
            component = documents["components"].get(component_id)
            if not component or component.get("domainId") != domain_id:
                failures.append(f"{label}.componentIds: {component_id!r} does not resolve reciprocally")
        for operation_id in require_list(document.get("operationIds"), f"{label}.operationIds", failures):
            operation = documents["operations"].get(operation_id)
            if not operation or operation.get("domainId") != domain_id:
                failures.append(f"{label}.operationIds: {operation_id!r} does not resolve reciprocally")

    for node_id, document in documents["nodes"].items():
        label = artifacts["nodes"][node_id]["path"]
        check_keys(
            document,
            {"schemaVersion", "id", "kind", "name", "responsibility", "technology", "identity", "certainty", "sourceFindings", "evidence"},
            {"subtype", "ownership"}, label, failures,
        )
        if document.get("kind") not in NODE_KINDS:
            failures.append(f"{label}.kind: invalid value")
        elif not valid_id(node_id, document.get("kind")):
            failures.append(f"{label}.id: node ID prefix must match its kind")
        validate_common_claim(document, label, source_ids, failures)

    for component_id, document in documents["components"].items():
        label = artifacts["components"][component_id]["path"]
        check_keys(
            document,
            {"schemaVersion", "id", "domainId", "ownerNodeId", "name", "responsibility", "technology", "operationIds", "certainty", "sourceFindings", "evidence"},
            {"interface"}, label, failures,
        )
        domain = documents["domains"].get(document.get("domainId"))
        if not domain or component_id not in domain.get("componentIds", []):
            failures.append(f"{label}.domainId: does not resolve reciprocally")
        owner = documents["nodes"].get(document.get("ownerNodeId"))
        if not owner or owner.get("kind") != "runtime":
            failures.append(f"{label}.ownerNodeId: must resolve to a runtime")
        for operation_id in require_list(document.get("operationIds"), f"{label}.operationIds", failures):
            operation = documents["operations"].get(operation_id)
            if not operation or component_id not in operation.get("ownerComponentIds", []):
                failures.append(f"{label}.operationIds: {operation_id!r} is not reciprocal")
        validate_common_claim(document, label, source_ids, failures)

    for interface_id, document in documents["interfaces"].items():
        label = artifacts["interfaces"][interface_id]["path"]
        required = {"schemaVersion", "id", "ownerNodeId", "kind", "purpose", "rules", "certainty", "coverage", "sourceFindings", "evidence"}
        optional = {"method", "path", "service", "version", "channel", "contract"}
        check_keys(document, required, optional, label, failures)
        if document.get("ownerNodeId") not in node_ids:
            failures.append(f"{label}.ownerNodeId: does not resolve")
        if document.get("kind") not in INTERFACE_KINDS:
            failures.append(f"{label}.kind: invalid value")
        coverage = document.get("coverage")
        check_keys(coverage, {"status", "operationPathIds", "reason", "gapIds"}, set(), f"{label}.coverage", failures)
        if isinstance(coverage, dict):
            status = coverage.get("status")
            path_ids = require_list(coverage.get("operationPathIds"), f"{label}.coverage.operationPathIds", failures)
            gap_ids = require_list(coverage.get("gapIds"), f"{label}.coverage.gapIds", failures)
            if status not in INTERFACE_COVERAGE_STATUSES:
                failures.append(f"{label}.coverage.status: invalid value")
            if status == "covered" and not path_ids:
                failures.append(f"{label}.coverage: covered requires operation paths")
            if status == "excluded" and (path_ids or gap_ids):
                failures.append(f"{label}.coverage: excluded cannot reference paths or gaps")
            if status == "unresolved" and not gap_ids:
                failures.append(f"{label}.coverage: unresolved requires gaps")
            for path_id in path_ids:
                if path_id not in documents["paths"]:
                    failures.append(f"{label}.coverage: path {path_id!r} does not resolve")
            for gap_id in gap_ids:
                if gap_id not in documents["gaps"]:
                    failures.append(f"{label}.coverage: gap {gap_id!r} does not resolve")
        validate_common_claim(document, label, source_ids, failures)

    for relationship_id, document in documents["relationships"].items():
        label = artifacts["relationships"][relationship_id]["path"]
        check_keys(
            document,
            {"schemaVersion", "id", "fromId", "toId", "kind", "purpose", "technology", "rules", "certainty", "sourceFindings", "evidence"},
            {"interfaceId", "contract"}, label, failures,
        )
        if document.get("fromId") not in node_ids or document.get("toId") not in node_ids:
            failures.append(f"{label}: relationship endpoints must resolve to nodes")
        if document.get("kind") not in RELATIONSHIP_KINDS:
            failures.append(f"{label}.kind: invalid value")
        if "interfaceId" in document and document.get("interfaceId") not in documents["interfaces"]:
            failures.append(f"{label}.interfaceId: does not resolve")
        validate_common_claim(document, label, source_ids, failures)

    for operation_id, document in documents["operations"].items():
        label = artifacts["operations"][operation_id]["path"]
        check_keys(
            document,
            {"schemaVersion", "id", "domainId", "name", "description", "ownerComponentIds", "triggerInterfaceIds", "pathIds"},
            set(), label, failures,
        )
        domain = documents["domains"].get(document.get("domainId"))
        if not domain or operation_id not in domain.get("operationIds", []):
            failures.append(f"{label}.domainId: does not resolve reciprocally")
        for component_id in require_list(document.get("ownerComponentIds"), f"{label}.ownerComponentIds", failures, non_empty=True):
            component = documents["components"].get(component_id)
            if not component or operation_id not in component.get("operationIds", []):
                failures.append(f"{label}.ownerComponentIds: {component_id!r} is not reciprocal")
        for interface_id in require_list(document.get("triggerInterfaceIds"), f"{label}.triggerInterfaceIds", failures, non_empty=True):
            if interface_id not in documents["interfaces"]:
                failures.append(f"{label}.triggerInterfaceIds: {interface_id!r} does not resolve")
        for path_id in require_list(document.get("pathIds"), f"{label}.pathIds", failures, non_empty=True):
            path_document = documents["paths"].get(path_id)
            if not path_document or path_document.get("operationId") != operation_id:
                failures.append(f"{label}.pathIds: {path_id!r} is not reciprocal")

    path_reviews = progress.get("pathReviews", {}) if isinstance(progress.get("pathReviews"), dict) else {}
    if set(path_reviews) != set(documents["paths"]):
        failures.append("progress.json.pathReviews: must exactly match operation paths")
    for path_id, document in documents["paths"].items():
        label = artifacts["paths"][path_id]["path"]
        check_keys(
            document,
            {"schemaVersion", "id", "operationId", "name", "kind", "description", "triggerInterfaceIds", "callers", "participants", "certainty", "sequence", "outcome", "coverage"},
            {"continuesFromPathIds", "causedByPathIds", "correlation"}, label, failures,
        )
        operation = documents["operations"].get(document.get("operationId"))
        if not operation or path_id not in operation.get("pathIds", []):
            failures.append(f"{label}.operationId: does not resolve reciprocally")
        if document.get("kind") not in PATH_KINDS:
            failures.append(f"{label}.kind: invalid value")
        if document.get("certainty") not in CERTAINTIES:
            failures.append(f"{label}.certainty: invalid value")
        path_triggers = require_list(document.get("triggerInterfaceIds"), f"{label}.triggerInterfaceIds", failures, non_empty=True)
        if operation and not set(path_triggers) <= set(operation.get("triggerInterfaceIds", [])):
            failures.append(f"{label}.triggerInterfaceIds: must be operation triggers")
        for interface_id in path_triggers:
            interface = documents["interfaces"].get(interface_id)
            if not interface:
                failures.append(f"{label}.triggerInterfaceIds: {interface_id!r} does not resolve")
            elif path_id not in interface.get("coverage", {}).get("operationPathIds", []):
                failures.append(f"{label}.triggerInterfaceIds: {interface_id!r} coverage is not reciprocal")
        for linked_field in ("continuesFromPathIds", "causedByPathIds"):
            for linked_id in document.get(linked_field, []):
                if linked_id not in documents["paths"]:
                    failures.append(f"{label}.{linked_field}: {linked_id!r} does not resolve")
        validate_sequence(
            path_id, document, all_elements, documents["interfaces"], documents["relationships"],
            documents["gaps"], source_ids, failures,
        )
        review = path_reviews.get(path_id, {})
        required_gates = {"canonicalPathValidated", "numberedSequenceGenerated", "asciiDiagramGenerated", "projectionsValidated"}
        check_keys(review, {"stage", "gates"}, set(), f"progress.pathReviews.{path_id}", failures)
        gates = review.get("gates", {}) if isinstance(review, dict) else {}
        if set(gates) != required_gates:
            failures.append(f"progress.pathReviews.{path_id}.gates: invalid gate set")
        if not allow_incomplete and (review.get("stage") != "complete" or not all(gates.values())):
            failures.append(f"progress.pathReviews.{path_id}: review is not complete")
        projection_root = root / "projections" / document.get("operationId", "unknown") / path_id
        expected = {
            "numbered-sequence.md": render_numbered(document),
            "sequence-diagram.txt": render_ascii(document),
        }
        for name, content in expected.items():
            path = projection_root / name
            if not path.is_file():
                failures.append(f"{path}: missing generated projection")
            elif path.read_text(encoding="utf-8") != content:
                failures.append(f"{path}: differs from deterministic rendering")

    for artifact_id, document in documents["gaps"].items():
        label = artifacts["gaps"][artifact_id]["path"]
        check_keys(
            document, {"schemaVersion", "id", "description", "impact", "searches", "sourceFindings"},
            set(), label, failures,
        )
        require_list(document.get("searches"), f"{label}.searches", failures, non_empty=True)
        validate_findings(document.get("sourceFindings"), f"{label}.sourceFindings", source_ids, failures)

    for artifact_id, document in documents["conflicts"].items():
        label = artifacts["conflicts"][artifact_id]["path"]
        check_keys(
            document, {"schemaVersion", "id", "description", "impact", "status", "alternatives", "sourceFindings"},
            {"resolution"}, label, failures,
        )
        if document.get("status") not in {"open", "resolved"}:
            failures.append(f"{label}.status: invalid value")
        if document.get("status") == "resolved" and not document.get("resolution"):
            failures.append(f"{label}.resolution: required for resolved conflicts")
        alternatives = require_list(document.get("alternatives"), f"{label}.alternatives", failures, non_empty=True)
        if len(alternatives) < 2:
            failures.append(f"{label}.alternatives: requires at least two alternatives")
        for index, alternative in enumerate(alternatives):
            item_label = f"{label}.alternatives[{index}]"
            check_keys(alternative, {"value", "sourceFindings"}, set(), item_label, failures)
            if isinstance(alternative, dict):
                validate_findings(alternative.get("sourceFindings"), f"{item_label}.sourceFindings", source_ids, failures)
        validate_findings(document.get("sourceFindings"), f"{label}.sourceFindings", source_ids, failures)

    expected_index = build_index_value(root, failures)
    actual_index = top_documents.get("index.json")
    if isinstance(actual_index, dict):
        if set(actual_index) != INDEX_KEYS:
            failures.append("index.json: invalid top-level keys")
        if actual_index != expected_index:
            failures.append("index.json: stale or inconsistent; run the index command")

    for collection, entries in artifacts.items():
        for artifact_id, entry in entries.items():
            path = root / entry["path"]
            document = documents[collection][artifact_id]
            if path.read_bytes() != canonical_bytes(document):
                failures.append(f"{entry['path']}: JSON is not canonically formatted")

    if failures:
        raise ValueError("\n".join(dict.fromkeys(failures)))
    return expected_index


def format_model(root):
    count = 0
    for path in sorted(root.rglob("*.json")):
        if path.name == "index.json":
            continue
        document = read_json(path)
        write_json(path, document)
        count += 1
    build_index(root)
    return count


def diff_indexes(before_path, after_path):
    before = read_json(before_path)
    after = read_json(after_path)
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "beforeSemanticHash": before.get("modelSemanticHash"),
        "afterSemanticHash": after.get("modelSemanticHash"),
        "added": [],
        "removed": [],
        "semanticChanges": [],
        "evidenceOnlyChanges": [],
        "projectionChanges": [],
        "controlChanges": [],
        "unchanged": 0,
    }
    before_artifacts = before.get("artifacts", {})
    after_artifacts = after.get("artifacts", {})
    collections = sorted(set(before_artifacts) | set(after_artifacts))
    for collection in collections:
        old = before_artifacts.get(collection, {})
        new = after_artifacts.get(collection, {})
        for artifact_id in sorted(set(old) | set(new)):
            key = f"{collection}:{artifact_id}"
            if artifact_id not in old:
                result["added"].append(key)
            elif artifact_id not in new:
                result["removed"].append(key)
            elif old[artifact_id].get("semanticHash") != new[artifact_id].get("semanticHash"):
                result["semanticChanges"].append(key)
            elif old[artifact_id].get("contentHash") != new[artifact_id].get("contentHash"):
                result["evidenceOnlyChanges"].append(key)
            else:
                result["unchanged"] += 1
    for field in ("subjectRef", "decisionsRef", "progressRef"):
        if before.get(field) != after.get(field):
            result["controlChanges"].append(field)
    old_projections = before.get("projections", {})
    new_projections = after.get("projections", {})
    for path_id in sorted(set(old_projections) | set(new_projections)):
        if old_projections.get(path_id) != new_projections.get(path_id):
            result["projectionChanges"].append(path_id)
    return result


def init(root, subject_name, sources):
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"not empty: {root}")
    domain_id = "domain." + slug(subject_name)
    source_records = []
    seen = set()
    for source in sources:
        source_id = "source." + slug(Path(source).stem)
        if source_id in seen:
            raise ValueError(f"source ID collision for {source!r}; initialize separately and assign stable source IDs")
        seen.add(source_id)
        source_records.append((source_id, source))
    for directory in ("domains", "nodes", "components", "interfaces", "relationships", "operations", "gaps", "conflicts", "sources", "projections", "changes"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    write_json(root / "subject.json", {
        "schemaVersion": SCHEMA_VERSION,
        "subject": {
            "id": domain_id,
            "name": subject_name,
            "description": f"Architecture model for {subject_name}",
            "aliases": [],
            "discoveryRoots": sources,
            "requestedSources": [source_id for source_id, _ in source_records],
            "exclusions": [],
        },
    })
    write_json(root / "decisions.json", {
        "schemaVersion": SCHEMA_VERSION,
        "identityOverrides": {},
        "targetOverrides": {},
        "repositoryOverrides": {},
        "systemBoundaries": {},
    })
    source_progress = {}
    for source_id, source in source_records:
        write_json(root / "sources" / source_id / "scan.json", {
            "schemaVersion": SCHEMA_VERSION,
            "id": source_id,
            "source": {
                "location": source,
                "repository": None,
                "revision": None,
                "branch": None,
                "status": "pending",
                "coverage": {"included": [], "excluded": [], "limitations": []},
            },
            "discoveredRepositories": [],
            "units": {},
            "components": {},
            "operations": {},
            "gaps": [],
        })
        source_progress[source_id] = {
            "stage": "pending",
            "gates": {
                "scanWritten": False,
                "scanValidated": False,
                "graphUpdated": False,
                "gapsReviewed": False,
                "conflictsReviewed": False,
            },
        }
    write_json(root / "domains" / f"{domain_id}.json", {
        "schemaVersion": SCHEMA_VERSION,
        "id": domain_id,
        "name": subject_name,
        "description": f"Architecture scope for {subject_name}",
        "sourceIds": [source_id for source_id, _ in source_records],
        "componentIds": [],
        "operationIds": [],
    })
    write_json(root / "progress.json", {
        "schemaVersion": SCHEMA_VERSION,
        "activeSourceId": None,
        "sources": source_progress,
        "pathReviews": {},
    })
    build_index(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    initialize = commands.add_parser("init", help="initialize a sharded model")
    initialize.add_argument("root", type=Path)
    initialize.add_argument("--subject", required=True)
    initialize.add_argument("--source", action="append", default=[])

    index = commands.add_parser("index", help="rebuild deterministic index.json")
    index.add_argument("root", type=Path)

    renderer = commands.add_parser("render", help="generate numbered and ASCII path projections")
    renderer.add_argument("root", type=Path)
    renderer.add_argument("--path-id")

    validator = commands.add_parser("validate", help="validate the complete sharded graph")
    validator.add_argument("root", type=Path)
    validator.add_argument("--allow-incomplete", action="store_true")

    formatter = commands.add_parser("format", help="canonicalize JSON and rebuild the index")
    formatter.add_argument("root", type=Path)

    differ = commands.add_parser("diff", help="classify changes between two generated indexes")
    differ.add_argument("before", type=Path)
    differ.add_argument("after", type=Path)
    differ.add_argument("--output", type=Path)

    arguments = parser.parse_args()
    try:
        if arguments.command == "init":
            root = long_path(arguments.root)
            init(root, arguments.subject, arguments.source)
            print(f"Initialized sharded architecture model: {arguments.root}")
        elif arguments.command == "index":
            result = build_index(long_path(arguments.root))
            print(f"Indexed architecture model: {result['modelSemanticHash']}")
        elif arguments.command == "render":
            count = render(long_path(arguments.root), arguments.path_id)
            print(f"Rendered {count} operation path(s)")
        elif arguments.command == "validate":
            result = validate(long_path(arguments.root), arguments.allow_incomplete)
            print(f"Valid sharded architecture model: {result['modelSemanticHash']}")
        elif arguments.command == "format":
            count = format_model(long_path(arguments.root))
            print(f"Canonicalized {count} JSON artifact(s)")
        elif arguments.command == "diff":
            result = diff_indexes(long_path(arguments.before), long_path(arguments.after))
            if arguments.output:
                write_json(long_path(arguments.output), result)
            else:
                sys.stdout.write(canonical_bytes(result).decode("utf-8"))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()

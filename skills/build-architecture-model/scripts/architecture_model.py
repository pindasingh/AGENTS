#!/usr/bin/env python3
"""Initialize and preflight architecture-model artifacts using only the stdlib."""

import argparse
import json
import re
from pathlib import Path

FLOW_ID = re.compile(r"flow\.[a-z0-9][a-z0-9._-]*")
SEQUENCE_NUMBER = re.compile(r"[1-9][0-9]*(?:\.[1-9][0-9]*)*")
MARKDOWN_STEP = re.compile(r"^\s*(\d+(?:\.\d+)*)(?:\.)?\s+\*\*(.*?)\*\*", re.MULTILINE)
ASCII_STEP = re.compile(r"^(\d+(?:\.\d+)*)\s+", re.MULTILINE)
ASCII_PARTICIPANT = re.compile(r"^\s+P(\d+)\s+(\S+)\s*$", re.MULTILINE)


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def init(root, subject, sources):
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"not empty: {root}")
    (root / "scans").mkdir(parents=True, exist_ok=True)
    (root / "flow-reviews").mkdir(parents=True, exist_ok=True)
    ids = [Path(source).stem.lower().replace(" ", "-") for source in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("source IDs are not unique")
    subject_record = {
        "schemaVersion": 1,
        "subject": {
            "id": subject.lower().replace(" ", "-"),
            "name": subject,
            "description": f"Architecture model for {subject}",
            "aliases": [],
            "requestedSources": sources,
            "exclusions": [],
        },
    }
    write(root / "subject.json", subject_record)
    write(
        root / "decisions.json",
        {"schemaVersion": 1, "identityOverrides": {}, "targetOverrides": {}, "systemBoundaries": {}},
    )
    gates = {
        "scanWritten": False,
        "scanValidated": False,
        "modelUpdated": False,
        "gapsReviewed": False,
        "conflictsReviewed": False,
    }
    progress_sources = {source: {"stage": "pending", "gates": dict(gates)} for source in sources}
    write(
        root / "progress.json",
        {"schemaVersion": 1, "activeSource": None, "flowReviews": {}, "sources": progress_sources},
    )
    write(
        root / "model.json",
        {
            "schemaVersion": 1,
            "subject": subject_record["subject"],
            "sources": {},
            "nodes": {},
            "components": {},
            "interfaces": {},
            "relationships": {},
            "flows": {},
            "flowCoverage": {},
            "systemBoundaries": {},
            "gaps": {},
            "conflicts": {},
        },
    )


def read_json(path, failures):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        failures.append(f"{path}: {error}")
        return None


def hierarchy_key(number):
    return tuple(int(part) for part in number.split("."))


def validate_sequence(flow_id, flow, failures):
    sequence = flow.get("sequence") if isinstance(flow, dict) else None
    if not isinstance(sequence, list) or not sequence:
        failures.append(f"{flow_id}: sequence must be a non-empty array")
        return [], []
    numbers, labels = [], []
    for index, step in enumerate(sequence):
        if not isinstance(step, dict):
            failures.append(f"{flow_id}: sequence[{index}] must be an object")
            continue
        number = step.get("number")
        if not isinstance(number, str) or not SEQUENCE_NUMBER.fullmatch(number):
            failures.append(f"{flow_id}: sequence[{index}] has an invalid number")
            continue
        numbers.append(number)
        kind = step.get("kind")
        label = step.get("name") if kind == "stage" else step.get("operation")
        if not isinstance(label, str) or not label.strip():
            failures.append(f"{flow_id}: {number} is missing its exact display label")
            label = ""
        labels.append(label)
        expected_parent = number.rsplit(".", 1)[0] if "." in number else None
        if step.get("parent") != expected_parent:
            failures.append(f"{flow_id}: {number} has parent {step.get('parent')!r}, expected {expected_parent!r}")
        if expected_parent and expected_parent not in numbers:
            failures.append(f"{flow_id}: {number} appears before its parent {expected_parent}")
    if len(numbers) != len(set(numbers)):
        failures.append(f"{flow_id}: sequence numbers are not unique")
    if numbers and numbers != sorted(numbers, key=hierarchy_key):
        failures.append(f"{flow_id}: sequence array is not in hierarchical numeric order")
    siblings = {}
    for number in numbers:
        parent = number.rsplit(".", 1)[0] if "." in number else ""
        siblings.setdefault(parent, []).append(int(number.rsplit(".", 1)[-1]))
    for parent, values in siblings.items():
        if values != list(range(1, len(values) + 1)):
            scope = parent or "root"
            failures.append(f"{flow_id}: {scope} sibling numbers are not contiguous")
    return numbers, labels


def participant_ids(flow_id, flow, failures):
    participants = flow.get("participants") if isinstance(flow, dict) else None
    if not isinstance(participants, list) or not participants:
        failures.append(f"{flow_id}: participants must be a non-empty array")
        return []
    ids = []
    for index, participant in enumerate(participants):
        participant_id = participant.get("id") if isinstance(participant, dict) else None
        if not isinstance(participant_id, str) or not participant_id:
            failures.append(f"{flow_id}: participants[{index}] has no ID")
        else:
            ids.append(participant_id)
    if len(ids) != len(set(ids)):
        failures.append(f"{flow_id}: participant IDs are not unique")
    return ids


def non_empty_list(value):
    return isinstance(value, list) and bool(value)


def validate_flow_model(flow_id, flow, model, failures):
    required = {
        "name", "scenario", "path", "description", "owner", "trigger", "callers",
        "participants", "certainty", "sequence", "outcome", "coverage",
    }
    if not isinstance(flow, dict) or not required <= set(flow):
        failures.append(f"{flow_id}: flow is missing required detailed fields")
        return
    nodes = model.get("nodes", {})
    components = model.get("components", {})
    interfaces = model.get("interfaces", {})
    relationships = model.get("relationships", {})
    elements = set(nodes) | set(components)
    if flow.get("owner") not in nodes:
        failures.append(f"{flow_id}: owner does not resolve to a model node")
    if flow.get("trigger") not in interfaces:
        failures.append(f"{flow_id}: trigger does not resolve to a model interface")

    participants = participant_ids(flow_id, flow, failures)
    if any(participant not in elements for participant in participants):
        failures.append(f"{flow_id}: every participant must resolve to a node or component")
    callers = flow.get("callers")
    if not isinstance(callers, list):
        failures.append(f"{flow_id}: callers must be an array")
        callers = []
    for index, caller in enumerate(callers):
        if not isinstance(caller, dict):
            failures.append(f"{flow_id}: callers[{index}] must be an object")
            continue
        if caller.get("nodeId") not in nodes or caller.get("relationshipId") not in relationships:
            failures.append(f"{flow_id}: callers[{index}] references an unknown node or relationship")
        if not non_empty_list(caller.get("sourceFindings")) or not non_empty_list(caller.get("evidence")):
            failures.append(f"{flow_id}: callers[{index}] requires source findings and evidence")

    numbers, _ = validate_sequence(flow_id, flow, failures)
    for step in flow.get("sequence", []):
        if not isinstance(step, dict):
            continue
        number = step.get("number", "?")
        if not non_empty_list(step.get("sourceFindings")) or not non_empty_list(step.get("evidence")):
            failures.append(f"{flow_id}: {number} requires source findings and evidence")
        if step.get("kind") == "stage":
            continue
        for field in ("operation", "input", "output", "boundary", "certainty", "continuation"):
            if not isinstance(step.get(field), str) or not step[field].strip():
                failures.append(f"{flow_id}: {number} requires non-empty {field}")
        forms = sum(
            (
                "at" in step,
                "source" in step and "destination" in step,
                "callerRelationshipIds" in step and "destination" in step,
                "callerRelationshipIds" in step and "source" in step and "destination" not in step,
            )
        )
        if forms != 1:
            failures.append(f"{flow_id}: {number} must use exactly one execution form")
        for endpoint in ("at", "source", "destination"):
            if endpoint in step and step[endpoint] not in elements:
                failures.append(f"{flow_id}: {number} {endpoint} does not resolve to a node or component")
        if "relationshipId" in step and step["relationshipId"] not in relationships:
            failures.append(f"{flow_id}: {number} relationshipId does not resolve")
        if "interfaceId" in step and step["interfaceId"] not in interfaces:
            failures.append(f"{flow_id}: {number} interfaceId does not resolve")

    outcome = flow.get("outcome")
    if not isinstance(outcome, dict) or outcome.get("at") not in numbers or not outcome.get("description"):
        failures.append(f"{flow_id}: outcome must describe and reference a sequence step")
    flow_coverage = flow.get("coverage")
    if not isinstance(flow_coverage, dict) or flow_coverage.get("status") not in {"complete", "partial", "blocked"}:
        failures.append(f"{flow_id}: coverage must have a valid status")


def header_value(text, prefix):
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip().strip("`")
    return None


def expected_endpoints(flow_id, flow, step, aliases, failures):
    if step.get("kind") == "stage":
        return None
    if "at" in step:
        endpoint = aliases.get(step["at"])
        if not endpoint:
            failures.append(f"{flow_id}: {step.get('number')} local endpoint is not a participant")
            return None
        return endpoint, endpoint
    if "source" in step and "destination" in step:
        source, destination = aliases.get(step["source"]), aliases.get(step["destination"])
        if not source or not destination:
            failures.append(f"{flow_id}: {step.get('number')} interaction endpoint is not a participant")
            return None
        return source, destination
    caller_relationships = step.get("callerRelationshipIds")
    if isinstance(caller_relationships, list) and caller_relationships:
        caller_nodes = {
            caller.get("relationshipId"): caller.get("nodeId")
            for caller in flow.get("callers", [])
            if isinstance(caller, dict)
        }
        caller_aliases = [aliases.get(caller_nodes.get(relationship)) for relationship in caller_relationships]
        if any(not alias for alias in caller_aliases):
            failures.append(f"{flow_id}: {step.get('number')} caller relationship does not resolve to a participant")
            return None
        callers = "|".join(caller_aliases)
        if "destination" in step:
            destination = aliases.get(step["destination"])
            if not destination:
                failures.append(f"{flow_id}: {step.get('number')} destination is not a participant")
                return None
            return callers, destination
        if "source" in step:
            source = aliases.get(step["source"])
            if not source:
                failures.append(f"{flow_id}: {step.get('number')} source is not a participant")
                return None
            return source, callers
    failures.append(f"{flow_id}: {step.get('number')} has no resolvable execution endpoints")
    return None


def validate_review(flow_id, flow, review, failures):
    markdown_path = review / "numbered-sequence.md"
    ascii_path = review / "sequence-diagram.txt"
    if not markdown_path.is_file():
        failures.append(f"{markdown_path}: missing flow review artifact")
        return
    if not ascii_path.is_file():
        failures.append(f"{ascii_path}: missing flow review artifact")
        return
    markdown = markdown_path.read_text(encoding="utf-8")
    ascii_diagram = ascii_path.read_text(encoding="utf-8")
    for path, text in ((markdown_path, markdown), (ascii_path, ascii_diagram)):
        if "{{" in text:
            failures.append(f"{path}: unresolved placeholder")
    if header_value(markdown, "- Flow ID:") != flow_id:
        failures.append(f"{markdown_path}: Flow ID does not match {flow_id}")
    if header_value(ascii_diagram, "Flow ID:") != flow_id:
        failures.append(f"{ascii_path}: Flow ID does not match {flow_id}")

    model_numbers, model_labels = validate_sequence(flow_id, flow, failures)
    markdown_steps = MARKDOWN_STEP.findall(markdown)
    markdown_numbers = [number for number, _ in markdown_steps]
    markdown_labels = [label for _, label in markdown_steps]
    ascii_numbers = ASCII_STEP.findall(ascii_diagram)
    if markdown_numbers != model_numbers:
        failures.append(f"{markdown_path}: sequence numbers/order differ from model.json")
    if ascii_numbers != model_numbers:
        failures.append(f"{ascii_path}: sequence numbers/order differ from model.json")
    if markdown_labels != model_labels:
        failures.append(f"{markdown_path}: stage/operation labels differ from model.json")
    participant_rows = ASCII_PARTICIPANT.findall(ascii_diagram)
    ascii_ids = [participant_id for _, participant_id in participant_rows]
    expected_alias_numbers = [str(index) for index in range(1, len(ascii_ids) + 1)]
    if [number for number, _ in participant_rows] != expected_alias_numbers:
        failures.append(f"{ascii_path}: participant aliases must be contiguous P1..Pn")
    aliases = {participant_id: f"P{index}" for index, participant_id in enumerate(ascii_ids, start=1)}
    for step, number, label in zip(flow.get("sequence", []), model_numbers, model_labels):
        line = next((item for item in ascii_diagram.splitlines() if item.startswith(number + " ")), "")
        if not line or label not in line:
            failures.append(f"{ascii_path}: {number} does not contain the exact model label")
        endpoints = expected_endpoints(flow_id, flow, step, aliases, failures)
        if endpoints:
            interaction = re.match(rf"^{re.escape(number)}\s+(\S+)\s+->\s+(\S+)\s+:\s", line)
            if not interaction or interaction.groups() != endpoints:
                failures.append(f"{ascii_path}: {number} endpoints/direction differ from model.json")

    model_participants = participant_ids(flow_id, flow, failures)
    markdown_participants = header_value(markdown, "- Participant IDs:")
    markdown_ids = markdown_participants.split(" | ") if markdown_participants else []
    if markdown_ids != model_participants:
        failures.append(f"{markdown_path}: participant IDs/order differ from model.json")
    if ascii_ids != model_participants:
        failures.append(f"{ascii_path}: participant IDs/order differ from model.json")


def validate(root):
    failures = []
    required = ["subject.json", "decisions.json", "progress.json", "model.json"]
    docs = {name: read_json(root / name, failures) for name in required}
    for path in sorted((root / "scans").glob("*.json")):
        docs[str(path)] = read_json(path, failures)
    for name, document in docs.items():
        if not isinstance(document, dict) or document.get("schemaVersion") != 1:
            failures.append(f"{name}: schemaVersion must be 1")

    model = docs.get("model.json") or {}
    expected = {
        "schemaVersion", "subject", "sources", "nodes", "components", "interfaces",
        "relationships", "flows", "flowCoverage", "systemBoundaries", "gaps", "conflicts",
    }
    if isinstance(model, dict) and set(model) != expected:
        failures.append("model.json: top-level keys do not match the closed contract")
    progress = docs.get("progress.json") or {}
    flows = model.get("flows", {}) if isinstance(model, dict) else {}
    reviews = progress.get("flowReviews", {}) if isinstance(progress, dict) else {}
    if not isinstance(flows, dict):
        failures.append("model.json: flows must be an object")
        flows = {}
    if not isinstance(reviews, dict) or set(flows) != set(reviews):
        failures.append("progress.json: flowReviews must exactly match model flows")
        reviews = reviews if isinstance(reviews, dict) else {}

    interfaces = model.get("interfaces", {}) if isinstance(model, dict) else {}
    coverage = model.get("flowCoverage", {}) if isinstance(model, dict) else {}
    gaps = model.get("gaps", {}) if isinstance(model, dict) else {}
    if not isinstance(interfaces, dict):
        failures.append("model.json: interfaces must be an object")
        interfaces = {}
    if not isinstance(coverage, dict) or set(coverage) != set(interfaces):
        failures.append("model.json: flowCoverage must exactly match model interfaces")
        coverage = coverage if isinstance(coverage, dict) else {}
    if not isinstance(gaps, dict):
        failures.append("model.json: gaps must be an object")
        gaps = {}
    for interface_id, record in coverage.items():
        if not isinstance(record, dict):
            failures.append(f"model.json: {interface_id} flow coverage must be an object")
            continue
        status = record.get("status")
        flow_ids = record.get("flowIds")
        if status not in {"covered", "excluded", "unresolved"}:
            failures.append(f"model.json: {interface_id} has invalid flow coverage status")
        if not isinstance(flow_ids, list) or any(flow_id not in flows for flow_id in flow_ids):
            failures.append(f"model.json: {interface_id} flowIds must resolve to model flows")
            continue
        if status == "covered" and not flow_ids:
            failures.append(f"model.json: {interface_id} covered flow coverage requires a flow")
        if status == "excluded" and flow_ids:
            failures.append(f"model.json: {interface_id} excluded flow coverage cannot reference a flow")
        if status == "unresolved":
            gap_ids = record.get("gapIds")
            if not isinstance(gap_ids, list) or not gap_ids or any(gap_id not in gaps for gap_id in gap_ids):
                failures.append(f"model.json: {interface_id} unresolved flow coverage requires resolved gapIds")

    for flow_id, flow in flows.items():
        if not FLOW_ID.fullmatch(flow_id):
            failures.append(f"{flow_id}: invalid or unsafe flow ID")
            continue
        review_progress = reviews.get(flow_id, {})
        gates = review_progress.get("gates", {}) if isinstance(review_progress, dict) else {}
        required_gates = {
            "canonicalFlowValidated", "numberedSequenceWritten", "asciiDiagramWritten", "projectionsValidated",
        }
        if review_progress.get("stage") != "complete" or set(gates) != required_gates or not all(gates.values()):
            failures.append(f"progress.json: {flow_id} review is not complete with all gates true")
        validate_flow_model(flow_id, flow, model, failures)
        validate_review(flow_id, flow, root / "flow-reviews" / flow_id, failures)

    if failures:
        raise ValueError("\n".join(failures))
    print(f"Valid architecture artifact set: {root}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("root", type=Path)
    initialize.add_argument("--subject", required=True)
    initialize.add_argument("--source", action="append", default=[])
    check = commands.add_parser("validate-json")
    check.add_argument("root", type=Path)
    arguments = parser.parse_args()
    try:
        init(arguments.root, arguments.subject, arguments.source) if arguments.command == "init" else validate(arguments.root)
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
